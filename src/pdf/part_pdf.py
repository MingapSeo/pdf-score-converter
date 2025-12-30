"""성부별 PDF 생성 모듈 (MuseScore 사용)"""

import subprocess
from pathlib import Path
from typing import Dict, Optional


def find_musescore() -> Optional[str]:
    """
    시스템에서 MuseScore 실행 파일 찾기

    Returns:
        MuseScore 실행 경로 (없으면 None)
    """
    # 가능한 MuseScore 경로들
    possible_paths = [
        "mscore",  # Homebrew symlink
        "/opt/homebrew/bin/mscore",
        "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
        "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
        "musescore",
    ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def musicxml_to_pdf(
    musicxml_path: str | Path,
    output_path: str | Path,
    musescore_path: Optional[str] = None
) -> Path:
    """
    MusicXML 파일을 PDF로 변환

    Args:
        musicxml_path: MusicXML 파일 경로
        output_path: 출력 PDF 파일 경로
        musescore_path: MuseScore 실행 파일 경로 (None이면 자동 탐색)

    Returns:
        생성된 PDF 파일 경로
    """
    musicxml_path = Path(musicxml_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not musicxml_path.exists():
        raise FileNotFoundError(f"MusicXML 파일을 찾을 수 없습니다: {musicxml_path}")

    # MuseScore 찾기
    if musescore_path is None:
        musescore_path = find_musescore()
        if musescore_path is None:
            raise RuntimeError(
                "MuseScore를 찾을 수 없습니다. "
                "brew install --cask musescore 로 설치하세요."
            )

    # MuseScore CLI로 PDF 생성
    cmd = [
        musescore_path,
        "-o", str(output_path),
        str(musicxml_path)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(f"PDF 생성 실패: {result.stderr}")

    if not output_path.exists():
        raise FileNotFoundError(f"PDF 파일이 생성되지 않았습니다: {output_path}")

    return output_path


def export_parts_pdf(
    parts_dir: str | Path,
    output_dir: str | Path,
    musescore_path: Optional[str] = None
) -> Dict[str, Path]:
    """
    디렉토리 내 모든 MusicXML 파일을 PDF로 변환

    Args:
        parts_dir: MusicXML 파일 디렉토리
        output_dir: PDF 출력 디렉토리
        musescore_path: MuseScore 실행 파일 경로

    Returns:
        파트명 → PDF 파일 경로 딕셔너리
    """
    parts_dir = Path(parts_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # .musicxml과 .xml 파일 모두 처리
    musicxml_files = list(parts_dir.glob("*.musicxml")) + list(parts_dir.glob("*.xml"))

    for musicxml_file in sorted(musicxml_files):
        part_name = musicxml_file.stem
        pdf_path = output_dir / f"{part_name}.pdf"

        print(f"  PDF 생성 중: {musicxml_file.name} → {pdf_path.name}")

        try:
            musicxml_to_pdf(musicxml_file, pdf_path, musescore_path)
            results[part_name] = pdf_path
        except Exception as e:
            print(f"  오류: {e}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])

        if input_path.is_dir():
            # 디렉토리: 모든 MusicXML → PDF
            output_dir = input_path.parent / "pdf"
            results = export_parts_pdf(input_path, output_dir)
            print(f"\n{len(results)}개 PDF 파일 생성됨")
        else:
            # 단일 파일
            output_path = input_path.with_suffix('.pdf')
            musicxml_to_pdf(input_path, output_path)
            print(f"PDF 저장됨: {output_path}")
