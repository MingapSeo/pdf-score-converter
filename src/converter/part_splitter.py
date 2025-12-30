"""성부 분리 모듈"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
from music21 import stream, note, chord, clef, instrument, meter, key


class VoiceType(Enum):
    """성부 타입"""
    SOPRANO = "soprano"
    ALTO = "alto"
    TENOR = "tenor"
    BASS = "bass"
    PIANO = "piano"
    VIOLIN = "violin"
    OTHER = "other"


# 합창 음색 설정 (MIDI program number)
VOICE_INSTRUMENTS = {
    VoiceType.SOPRANO: 52,  # Choir Aahs
    VoiceType.ALTO: 52,
    VoiceType.TENOR: 52,
    VoiceType.BASS: 52,
    VoiceType.PIANO: 0,     # Acoustic Grand Piano
    VoiceType.VIOLIN: 40,   # Violin
    VoiceType.OTHER: 52,
}


def detect_voice_type(part: stream.Part, part_index: int, total_parts: int) -> VoiceType:
    """
    파트의 성부 타입을 추정

    Args:
        part: music21 Part 객체
        part_index: 파트 인덱스
        total_parts: 전체 파트 수

    Returns:
        추정된 VoiceType
    """
    part_name = (part.partName or "").lower()

    # 이름으로 추정
    if "soprano" in part_name or "sop" in part_name:
        return VoiceType.SOPRANO
    elif "alto" in part_name:
        return VoiceType.ALTO
    elif "tenor" in part_name or "ten" in part_name:
        return VoiceType.TENOR
    elif "bass" in part_name or "bas" in part_name:
        return VoiceType.BASS
    elif "piano" in part_name:
        return VoiceType.PIANO
    elif "violin" in part_name or "vln" in part_name:
        return VoiceType.VIOLIN

    # 음자리표로 추정
    clefs = part.getElementsByClass('Clef')
    if clefs:
        clef_obj = clefs[0]
        if isinstance(clef_obj, clef.TrebleClef):
            # 높은음자리표: 소프라노/알토 또는 바이올린
            if total_parts == 4:
                return VoiceType.SOPRANO if part_index < 2 else VoiceType.ALTO
            return VoiceType.SOPRANO
        elif isinstance(clef_obj, clef.BassClef):
            # 낮은음자리표: 테너/베이스
            if total_parts == 4:
                return VoiceType.TENOR if part_index < 3 else VoiceType.BASS
            return VoiceType.BASS

    return VoiceType.OTHER


def extract_voice(
    part: stream.Part,
    voice_id: Optional[int] = None,
    voice_type: VoiceType = VoiceType.OTHER
) -> stream.Part:
    """
    파트에서 특정 성부(voice)를 추출

    Args:
        part: 원본 파트
        voice_id: 추출할 voice ID (None이면 모든 음표)
        voice_type: 성부 타입

    Returns:
        추출된 파트
    """
    new_part = stream.Part()
    new_part.partName = voice_type.value.capitalize()

    # 악기 설정
    inst = instrument.Instrument()
    inst.midiProgram = VOICE_INSTRUMENTS.get(voice_type, 52)
    new_part.insert(0, inst)

    for measure in part.getElementsByClass('Measure'):
        new_measure = stream.Measure(number=measure.number)

        # 박자표, 조표 복사
        for ts in measure.getElementsByClass('TimeSignature'):
            new_measure.insert(ts.offset, ts)
        for ks in measure.getElementsByClass('KeySignature'):
            new_measure.insert(ks.offset, ks)
        for c in measure.getElementsByClass('Clef'):
            new_measure.insert(c.offset, c)

        # 음표/쉼표 추출
        if voice_id is not None and measure.hasVoices():
            # 특정 voice만 추출
            for voice in measure.voices:
                if voice.id == voice_id or str(voice.id) == str(voice_id):
                    for elem in voice.notesAndRests:
                        new_measure.insert(elem.offset, elem)
        else:
            # 모든 음표 복사
            for elem in measure.notesAndRests:
                new_measure.insert(elem.offset, elem)

        new_part.append(new_measure)

    return new_part


def split_grand_staff(part: stream.Part) -> Tuple[stream.Part, stream.Part]:
    """
    대보표(Grand Staff)를 상단/하단으로 분리

    합창 악보에서 소프라노+알토 또는 테너+베이스가 하나의 대보표에 있는 경우,
    음역대를 기준으로 분리

    Args:
        part: 대보표 파트

    Returns:
        (상단 파트, 하단 파트) 튜플
    """
    upper_part = stream.Part()
    lower_part = stream.Part()

    upper_part.partName = "Upper"
    lower_part.partName = "Lower"

    for measure in part.getElementsByClass('Measure'):
        upper_measure = stream.Measure(number=measure.number)
        lower_measure = stream.Measure(number=measure.number)

        # 메타데이터 복사
        for ts in measure.getElementsByClass('TimeSignature'):
            upper_measure.insert(ts.offset, ts)
            lower_measure.insert(ts.offset, ts)

        for elem in measure.notesAndRests:
            if isinstance(elem, chord.Chord):
                # 화음: 음역대로 분리
                upper_notes = []
                lower_notes = []

                for n in elem.notes:
                    if n.pitch.midi >= 60:  # Middle C 이상
                        upper_notes.append(n)
                    else:
                        lower_notes.append(n)

                if upper_notes:
                    if len(upper_notes) == 1:
                        upper_measure.insert(elem.offset, upper_notes[0])
                    else:
                        upper_measure.insert(elem.offset, chord.Chord(upper_notes))

                if lower_notes:
                    if len(lower_notes) == 1:
                        lower_measure.insert(elem.offset, lower_notes[0])
                    else:
                        lower_measure.insert(elem.offset, chord.Chord(lower_notes))

            elif isinstance(elem, note.Note):
                # 단일 음표: 음역대로 분류
                if elem.pitch.midi >= 60:
                    upper_measure.insert(elem.offset, elem)
                else:
                    lower_measure.insert(elem.offset, elem)

            elif isinstance(elem, note.Rest):
                # 쉼표: 양쪽에 복사
                upper_measure.insert(elem.offset, elem)
                lower_measure.insert(elem.offset, elem)

        upper_part.append(upper_measure)
        lower_part.append(lower_measure)

    return upper_part, lower_part


def split_parts(
    score: stream.Score,
    output_dir: str | Path,
    voice_types: Optional[Dict[int, VoiceType]] = None
) -> Dict[VoiceType, Path]:
    """
    악보를 성부별로 분리하여 저장

    Args:
        score: music21 Score 객체
        output_dir: 출력 디렉토리
        voice_types: 파트 인덱스 → VoiceType 매핑 (None이면 자동 감지)

    Returns:
        VoiceType → 파일 경로 딕셔너리
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    total_parts = len(score.parts)

    for i, part in enumerate(score.parts):
        # 성부 타입 결정
        if voice_types and i in voice_types:
            vtype = voice_types[i]
        else:
            vtype = detect_voice_type(part, i, total_parts)

        # 새 악보 생성
        new_score = stream.Score()

        # 메타데이터 복사
        if score.metadata:
            new_score.metadata = score.metadata

        # 파트 추출 및 추가
        extracted_part = extract_voice(part, voice_type=vtype)
        new_score.append(extracted_part)

        # 파일 저장
        output_path = output_dir / f"{vtype.value}.musicxml"
        new_score.write('musicxml', fp=str(output_path))
        results[vtype] = output_path

        print(f"  저장됨: {output_path.name}")

    return results


def split_satb(
    score: stream.Score,
    output_dir: str | Path
) -> Dict[str, Path]:
    """
    4부 합창 악보(SATB)를 각 성부로 분리

    Args:
        score: music21 Score 객체
        output_dir: 출력 디렉토리

    Returns:
        성부명 → 파일 경로 딕셔너리
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    parts = list(score.parts)

    # 파트 수에 따른 처리
    if len(parts) == 4:
        # 이상적인 경우: 4개 파트 = SATB
        voice_names = ["soprano", "alto", "tenor", "bass"]
        for i, (part, name) in enumerate(zip(parts, voice_names)):
            new_score = stream.Score()
            extracted = extract_voice(part, voice_type=VoiceType(name))
            new_score.append(extracted)

            output_path = output_dir / f"{name}.musicxml"
            new_score.write('musicxml', fp=str(output_path))
            results[name] = output_path
            print(f"  저장됨: {output_path.name}")

    elif len(parts) == 2:
        # 2개 파트: 대보표 2개 (SA + TB)
        # 각 대보표를 상단/하단으로 분리
        upper1, lower1 = split_grand_staff(parts[0])
        upper2, lower2 = split_grand_staff(parts[1])

        for part, name in [(upper1, "soprano"), (lower1, "alto"),
                           (upper2, "tenor"), (lower2, "bass")]:
            new_score = stream.Score()
            part.partName = name.capitalize()
            new_score.append(part)

            output_path = output_dir / f"{name}.musicxml"
            new_score.write('musicxml', fp=str(output_path))
            results[name] = output_path
            print(f"  저장됨: {output_path.name}")

    else:
        # 기타 경우: 그대로 분리
        for i, part in enumerate(parts):
            new_score = stream.Score()
            new_score.append(part)

            output_path = output_dir / f"part_{i+1}.musicxml"
            new_score.write('musicxml', fp=str(output_path))
            results[f"part_{i+1}"] = output_path
            print(f"  저장됨: {output_path.name}")

    return results


if __name__ == "__main__":
    import sys
    from .musicxml_parser import parse_musicxml, print_score_info

    if len(sys.argv) > 1:
        score = parse_musicxml(sys.argv[1])
        print_score_info(score)

        output_dir = Path(sys.argv[1]).parent / "split_parts"
        print(f"\n성부 분리 중...")
        results = split_satb(score, output_dir)
        print(f"\n{len(results)}개 성부 분리 완료")
