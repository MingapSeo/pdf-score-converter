"""PDF를 이미지로 변환하는 모듈"""

from pathlib import Path
from typing import List
from pdf2image import convert_from_path
from PIL import Image


def pdf_to_images(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    dpi: int = 300,
    fmt: str = "png"
) -> List[Path]:
    """
    PDF 파일을 페이지별 이미지로 변환

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리 (None이면 PDF와 같은 위치)
        dpi: 이미지 해상도 (기본 300dpi - OMR에 적합)
        fmt: 출력 형식 (png, jpg)

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_images"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # PDF를 이미지로 변환
    images: List[Image.Image] = convert_from_path(
        pdf_path,
        dpi=dpi,
        fmt=fmt
    )

    # 이미지 저장
    output_paths: List[Path] = []
    for i, image in enumerate(images, start=1):
        output_path = output_dir / f"page_{i:03d}.{fmt}"
        image.save(output_path, fmt.upper())
        output_paths.append(output_path)
        print(f"  저장됨: {output_path.name}")

    return output_paths


if __name__ == "__main__":
    # 테스트
    import sys
    if len(sys.argv) > 1:
        paths = pdf_to_images(sys.argv[1])
        print(f"\n총 {len(paths)}개 이미지 생성됨")
