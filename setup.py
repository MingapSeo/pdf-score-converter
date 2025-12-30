"""PDF Score Converter 패키지 설정"""

from setuptools import setup, find_packages

setup(
    name="pdf-score-converter",
    version="0.1.0",
    description="PDF 합창 악보를 각 성부(SATB)별로 분리하고 MIDI/음원으로 변환하는 CLI 도구",
    author="MingapSeo",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.0",
        "music21>=9.1.0",
        "mido>=1.3.0",
        "midi2audio>=0.1.1",
        "pdf2image>=1.16.0",
        "PyPDF2>=3.0.0",
        "Pillow>=10.0.0",
        "oemer>=0.1.5",
    ],
    entry_points={
        "console_scripts": [
            "score-converter=src.cli:main",
        ],
    },
)
