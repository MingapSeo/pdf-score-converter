"""Audiveris OMR 엔진 래퍼 모듈"""

import subprocess
from pathlib import Path
from typing import List, Optional


# Audiveris 실행 파일 경로
AUDIVERIS_PATHS = [
    "/Applications/Audiveris.app/Contents/MacOS/Audiveris",
    "/usr/local/bin/audiveris",
    "audiveris",
]


def find_audiveris() -> Optional[str]:
    """
    시스템에서 Audiveris 실행 파일 찾기

    Returns:
        Audiveris 실행 경로 (없으면 None)
    """
    for path in AUDIVERIS_PATHS:
        try:
            result = subprocess.run(
                [path, "-help"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def recognize_pdf(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    sheets: Optional[List[int]] = None
) -> List[Path]:
    """
    PDF 파일에서 악보를 인식하여 MusicXML로 변환

    Args:
        pdf_path: PDF 악보 파일 경로
        output_dir: 출력 디렉토리 (None이면 PDF와 같은 위치)
        sheets: 처리할 페이지 번호 리스트 (None이면 전체)

    Returns:
        생성된 MusicXML 파일 경로 리스트
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_output"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Audiveris 찾기
    audiveris_path = find_audiveris()
    if audiveris_path is None:
        raise RuntimeError(
            "Audiveris를 찾을 수 없습니다. "
            "/Applications/Audiveris.app이 설치되어 있는지 확인하세요."
        )

    # Audiveris CLI 실행
    cmd = [
        audiveris_path,
        "-batch",           # GUI 없이 실행
        "-transcribe",      # 전체 인식
        "-export",          # MusicXML 내보내기
        "-output", str(output_dir),
        str(pdf_path)
    ]

    if sheets:
        # 특정 페이지만 처리
        sheets_str = " ".join(str(s) for s in sheets)
        cmd.insert(-1, "-sheets")
        cmd.insert(-1, sheets_str)

    print(f"  Audiveris 실행 중: {pdf_path.name}")
    print(f"  출력 디렉토리: {output_dir}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600  # 10분 타임아웃
    )

    if result.returncode != 0:
        # Audiveris는 경고가 있어도 0이 아닌 코드를 반환할 수 있음
        # MusicXML 파일이 생성되었는지 확인
        pass

    # 출력 파일 찾기
    # Audiveris는 {pdf_stem}/{pdf_stem}.mxl 또는 .musicxml로 저장
    book_dir = output_dir / pdf_path.stem

    musicxml_files = []

    # .mxl (압축) 파일 찾기
    mxl_files = list(book_dir.glob("*.mxl")) if book_dir.exists() else []

    # .musicxml 파일 찾기
    xml_files = list(book_dir.glob("*.musicxml")) if book_dir.exists() else []

    # opus 파일 (전체 악보) 찾기
    opus_files = list(book_dir.glob("*.opus.mxl")) if book_dir.exists() else []

    musicxml_files = mxl_files + xml_files

    if not musicxml_files:
        # 다른 위치에서 찾기
        musicxml_files = list(output_dir.glob("**/*.mxl")) + list(output_dir.glob("**/*.musicxml"))

    if not musicxml_files:
        error_msg = f"MusicXML 출력 파일을 찾을 수 없습니다.\n"
        error_msg += f"Audiveris stdout:\n{result.stdout}\n"
        error_msg += f"Audiveris stderr:\n{result.stderr}"
        raise FileNotFoundError(error_msg)

    return sorted(musicxml_files)


def recognize_score(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    dpi: int = 300  # Audiveris에서는 사용하지 않지만 인터페이스 호환성 유지
) -> List[Path]:
    """
    PDF 악보 파일을 인식하여 MusicXML로 변환 (통합 함수)

    oemer_wrapper와 동일한 인터페이스 제공

    Args:
        pdf_path: PDF 악보 파일 경로
        output_dir: 출력 디렉토리
        dpi: PDF 변환 해상도 (Audiveris에서는 무시됨)

    Returns:
        생성된 MusicXML 파일 경로 리스트
    """
    return recognize_pdf(pdf_path, output_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        results = recognize_pdf(input_path)
        print(f"\n결과: {len(results)}개 파일 생성됨")
        for r in results:
            print(f"  - {r}")
