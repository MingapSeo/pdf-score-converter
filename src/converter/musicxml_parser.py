"""MusicXML 파싱 모듈"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from music21 import converter, stream, instrument


@dataclass
class PartInfo:
    """파트 정보"""
    index: int
    name: str
    instrument_name: str
    measure_count: int
    voice_count: int
    clef: str


@dataclass
class ScoreInfo:
    """악보 정보"""
    title: Optional[str]
    composer: Optional[str]
    parts: List[PartInfo]
    total_measures: int
    time_signature: str
    key_signature: str


def parse_musicxml(file_path: str | Path) -> stream.Score:
    """
    MusicXML 파일을 파싱하여 music21 Score 객체로 반환

    Args:
        file_path: MusicXML 파일 경로

    Returns:
        music21 Score 객체
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"MusicXML 파일을 찾을 수 없습니다: {file_path}")

    return converter.parse(str(file_path))


def get_score_info(score: stream.Score) -> ScoreInfo:
    """
    악보의 상세 정보를 추출

    Args:
        score: music21 Score 객체

    Returns:
        ScoreInfo 객체
    """
    # 메타데이터 추출
    title = None
    composer = None
    if score.metadata:
        title = score.metadata.title
        composer = score.metadata.composer

    # 파트 정보 추출
    parts_info = []
    for i, part in enumerate(score.parts):
        # 성부(voice) 수 계산
        voices = set()
        for measure in part.getElementsByClass('Measure'):
            for voice in measure.voices:
                voices.add(voice.id)
        voice_count = len(voices) if voices else 1

        # 음자리표 추출
        clefs = part.getElementsByClass('Clef')
        clef_name = clefs[0].sign if clefs else "Unknown"

        part_info = PartInfo(
            index=i,
            name=part.partName or f"Part {i+1}",
            instrument_name=str(part.getInstrument()) if part.getInstrument() else "Unknown",
            measure_count=len(part.getElementsByClass('Measure')),
            voice_count=voice_count,
            clef=clef_name
        )
        parts_info.append(part_info)

    # 박자표 추출
    time_sigs = score.flatten().getElementsByClass('TimeSignature')
    time_sig = f"{time_sigs[0].numerator}/{time_sigs[0].denominator}" if time_sigs else "4/4"

    # 조표 추출
    key_sigs = score.flatten().getElementsByClass('KeySignature')
    key_sig = str(key_sigs[0].sharps) + " sharps/flats" if key_sigs else "C major"

    # 총 마디 수
    total_measures = max(p.measure_count for p in parts_info) if parts_info else 0

    return ScoreInfo(
        title=title,
        composer=composer,
        parts=parts_info,
        total_measures=total_measures,
        time_signature=time_sig,
        key_signature=key_sig
    )


def print_score_info(score: stream.Score) -> None:
    """악보 정보를 출력"""
    info = get_score_info(score)

    print("=" * 50)
    print("악보 정보")
    print("=" * 50)

    if info.title:
        print(f"제목: {info.title}")
    if info.composer:
        print(f"작곡가: {info.composer}")

    print(f"박자: {info.time_signature}")
    print(f"조성: {info.key_signature}")
    print(f"총 마디: {info.total_measures}")
    print()

    print("파트 목록:")
    print("-" * 50)
    for part in info.parts:
        print(f"  [{part.index}] {part.name}")
        print(f"      악기: {part.instrument_name}")
        print(f"      음자리표: {part.clef}")
        print(f"      마디 수: {part.measure_count}")
        print(f"      성부 수: {part.voice_count}")
    print("=" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        score = parse_musicxml(sys.argv[1])
        print_score_info(score)
