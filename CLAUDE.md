# PDF Score Converter

PDF 합창 악보를 각 성부(SATB)별로 분리하고 MIDI/음원으로 변환하는 CLI 도구

## 프로젝트 목표

성당 합창단원이 PDF 악보에서 자신의 파트만 추출하여 연습용 음원을 만들 수 있도록 지원

## 기술 스택

- **언어**: Python 3.11+
- **OMR 엔진**: oemer (Python 딥러닝 기반 OMR)
- **음악 처리**: music21, mido
- **음원 생성**: FluidSynth + SoundFont (합창 음색)
- **PDF 처리**: pdf2image, PyPDF2
- **인터페이스**: CLI (click)

## 워크플로우

```
┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────┐
│  PDF    │ -> │  oemer    │ -> │ MusicXML │ -> │ 성부 분리    │ -> │ 출력     │
│  악보   │    │  (OMR)    │    │          │    │ (music21)   │    │          │
└─────────┘    └───────────┘    └──────────┘    └─────────────┘    └──────────┘
                                                                        │
                                                    ┌───────────────────┼───────────────────┐
                                                    ▼                   ▼                   ▼
                                               ┌─────────┐        ┌──────────┐       ┌───────────┐
                                               │  MIDI   │        │ MP3/WAV  │       │ 성부별 PDF│
                                               │         │        │ (합창음색)│       │           │
                                               └─────────┘        └──────────┘       └───────────┘
```

## 출력 형식

1. **MIDI**: 각 성부별 개별 파일 + 전체 합본
2. **MP3/WAV**: 합창 음색으로 렌더링된 음원
3. **성부별 PDF**: 각 파트만 추출한 악보

## 프로젝트 구조

```
pdf-score-converter/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── setup.py
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI 진입점
│   ├── omr/
│   │   ├── __init__.py
│   │   └── oemer_wrapper.py # oemer OMR 연동
│   ├── converter/
│   │   ├── __init__.py
│   │   ├── musicxml.py     # MusicXML 파싱
│   │   ├── part_splitter.py # 성부 분리 로직
│   │   └── midi_export.py  # MIDI 변환
│   ├── audio/
│   │   ├── __init__.py
│   │   └── synthesizer.py  # FluidSynth 음원 생성
│   └── pdf/
│       ├── __init__.py
│       └── part_pdf.py     # 성부별 PDF 생성
├── soundfonts/
│   └── .gitkeep            # 합창 SoundFont 저장 위치
├── tests/
│   └── __init__.py
└── output/                 # 변환 결과 저장
    └── .gitkeep
```

## CLI 사용법

```bash
# 기본 사용법: PDF를 모든 형식으로 변환
python -m src.cli convert "내 발을 씻기신 예수.pdf"

# 특정 출력 형식만 선택
python -m src.cli convert score.pdf --output midi
python -m src.cli convert score.pdf --output mp3
python -m src.cli convert score.pdf --output pdf

# 특정 성부만 추출
python -m src.cli convert score.pdf --parts soprano,alto

# 악보 구조 미리보기 (OMR 결과 확인)
python -m src.cli analyze score.pdf
```

## 의존성

### Python 패키지
- oemer: 딥러닝 기반 OMR (악보 인식)
- music21: MusicXML 파싱 및 음악 데이터 처리
- mido: MIDI 파일 생성
- midi2audio: MIDI를 오디오로 변환
- pdf2image: PDF를 이미지로 변환
- PyPDF2: PDF 조작
- click: CLI 프레임워크

### 외부 도구 (Homebrew로 설치)
- FluidSynth: MIDI 음원 합성 (`brew install fluid-synth`)
- Poppler: PDF 렌더링 (`brew install poppler`)

## 개발 현황

- [x] 요구사항 정의
- [x] 기술 스택 결정
- [x] 프로젝트 구조 생성
- [x] 환경 설정 (oemer, FluidSynth, Poppler 설치)
- [ ] OMR 파이프라인 구현
- [ ] MusicXML 파싱 및 성부 분리 구현
- [ ] MIDI 변환 구현
- [ ] 음원 생성 구현 (합창 음색)
- [ ] 성부별 PDF 생성 구현
- [ ] CLI 완성
- [ ] 테스트

## 알려진 제한사항

- OMR 정확도는 악보 품질에 따라 달라짐
- 복잡한 악보(셋잇단음표, 임시표 등)는 수동 수정 필요할 수 있음
- 합창 SoundFont 품질에 따라 음원 품질 결정됨

## 명령어 (개발용)

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt

# 외부 도구 설치 (macOS)
brew install fluid-synth poppler

# 테스트 실행
pytest tests/

# oemer 설치 확인
python -c "import oemer; print('oemer OK')"
```

## SoundFont 정보

합창 음색을 위해 다음 SoundFont 중 하나 사용 권장:
- FluidR3_GM.sf2 (기본, 합창 음색 포함)
- Choir Aahs 전용 SoundFont

## 참고 자료

- [oemer GitHub](https://github.com/BreezeWhite/oemer) - Python 딥러닝 OMR
- [music21 Documentation](https://web.mit.edu/music21/doc/)
- [FluidSynth](https://www.fluidsynth.org/)
- [MIDI Instrument List](https://en.wikipedia.org/wiki/General_MIDI#Program_change_events)
  - 52: Choir Aahs
  - 53: Voice Oohs
