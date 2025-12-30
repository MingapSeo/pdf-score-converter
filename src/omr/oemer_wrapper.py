"""oemer OMR 엔진 래퍼 모듈"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def recognize_image(
    image_path: str | Path,
    output_dir: str | Path | None = None,
    use_cache: bool = False
) -> Path:
    """
    단일 이미지에서 악보를 인식하여 MusicXML로 변환

    Args:
        image_path: 악보 이미지 경로
        output_dir: 출력 디렉토리 (None이면 이미지와 같은 위치)
        use_cache: 캐시 사용 여부 (이전 예측 결과 재사용)

    Returns:
        생성된 MusicXML 파일 경로
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    if output_dir is None:
        output_dir = image_path.parent
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # oemer CLI 실행
    cmd = [
        "oemer",
        str(image_path),
        "-o", str(output_dir)
    ]

    if use_cache:
        cmd.append("--save-cache")

    print(f"  oemer 실행 중: {image_path.name}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"oemer 실행 실패:\n{result.stderr}")

    # 출력 파일 찾기 (oemer는 {이미지명}.musicxml 로 저장)
    output_path = output_dir / f"{image_path.stem}.musicxml"

    if not output_path.exists():
        # 다른 가능한 이름 확인
        possible_outputs = list(output_dir.glob("*.musicxml"))
        if possible_outputs:
            output_path = possible_outputs[-1]  # 가장 최근 파일
        else:
            raise FileNotFoundError(
                f"MusicXML 출력 파일을 찾을 수 없습니다. oemer 출력:\n{result.stdout}"
            )

    return output_path


def recognize_images(
    image_paths: List[str | Path],
    output_dir: str | Path | None = None,
    use_cache: bool = False
) -> List[Path]:
    """
    여러 이미지에서 악보를 인식

    Args:
        image_paths: 악보 이미지 경로 리스트
        output_dir: 출력 디렉토리
        use_cache: 캐시 사용 여부

    Returns:
        생성된 MusicXML 파일 경로 리스트
    """
    results = []

    for i, image_path in enumerate(image_paths, start=1):
        print(f"[{i}/{len(image_paths)}] 악보 인식 중...")
        try:
            result = recognize_image(image_path, output_dir, use_cache)
            results.append(result)
            print(f"  완료: {result.name}")
        except Exception as e:
            print(f"  실패: {e}")

    return results


def recognize_score(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    dpi: int = 300
) -> List[Path]:
    """
    PDF 악보 파일을 인식하여 MusicXML로 변환 (통합 함수)

    Args:
        pdf_path: PDF 악보 파일 경로
        output_dir: 출력 디렉토리
        dpi: PDF 변환 해상도

    Returns:
        생성된 MusicXML 파일 경로 리스트
    """
    from src.pdf import pdf_to_images

    pdf_path = Path(pdf_path)

    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_output"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"1단계: PDF를 이미지로 변환 중...")
    image_dir = output_dir / "images"
    image_paths = pdf_to_images(pdf_path, image_dir, dpi=dpi)
    print(f"  {len(image_paths)}개 페이지 변환 완료\n")

    print(f"2단계: 악보 인식 (OMR) 중...")
    musicxml_dir = output_dir / "musicxml"
    musicxml_paths = recognize_images(image_paths, musicxml_dir)
    print(f"  {len(musicxml_paths)}개 MusicXML 생성 완료\n")

    return musicxml_paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])

        if input_path.suffix.lower() == ".pdf":
            results = recognize_score(input_path)
        else:
            results = [recognize_image(input_path)]

        print(f"\n결과: {len(results)}개 파일 생성됨")
        for r in results:
            print(f"  - {r}")
