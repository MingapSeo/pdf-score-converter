"""OMR (Optical Music Recognition) 모듈

지원 엔진:
- Audiveris (기본값): Java 기반, 빠름, PDF 직접 처리
- oemer: Python 딥러닝 기반, 느리지만 설치 간편
"""

# Audiveris를 기본으로 사용 (더 빠름)
try:
    from .audiveris_wrapper import recognize_score, recognize_pdf
    OMR_ENGINE = "audiveris"
except ImportError:
    from .oemer_wrapper import recognize_score
    from .oemer_wrapper import recognize_images
    OMR_ENGINE = "oemer"

__all__ = ["recognize_score", "OMR_ENGINE"]
