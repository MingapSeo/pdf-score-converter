"""MIDI 내보내기 모듈"""

from pathlib import Path
from typing import Dict, List, Optional
from music21 import stream, midi, tempo, instrument


# 합창 음색 MIDI 프로그램 번호
CHOIR_PROGRAM = 52  # Choir Aahs


def set_choir_instrument(score: stream.Score, program: int = CHOIR_PROGRAM) -> stream.Score:
    """
    악보의 모든 파트에 합창 음색 설정

    Args:
        score: music21 Score 객체
        program: MIDI 프로그램 번호 (기본: 52 - Choir Aahs)

    Returns:
        수정된 Score 객체
    """
    for part in score.parts:
        # 기존 악기 제거
        for inst in part.getElementsByClass(instrument.Instrument):
            part.remove(inst)

        # 합창 악기 추가
        choir = instrument.Instrument()
        choir.midiProgram = program
        part.insert(0, choir)

    return score


def export_midi(
    score: stream.Score,
    output_path: str | Path,
    tempo_bpm: Optional[int] = None,
    use_choir_sound: bool = True
) -> Path:
    """
    악보를 MIDI 파일로 내보내기

    Args:
        score: music21 Score 객체
        output_path: 출력 파일 경로
        tempo_bpm: 템포 (None이면 악보 원본 템포 사용)
        use_choir_sound: 합창 음색 사용 여부

    Returns:
        생성된 MIDI 파일 경로
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 악보 복사 (원본 수정 방지)
    score_copy = score.__deepcopy__()

    # 템포 설정
    if tempo_bpm:
        # 기존 템포 제거
        for t in score_copy.flatten().getElementsByClass(tempo.MetronomeMark):
            score_copy.remove(t, recurse=True)
        # 새 템포 추가
        mm = tempo.MetronomeMark(number=tempo_bpm)
        score_copy.insert(0, mm)

    # 합창 음색 설정
    if use_choir_sound:
        set_choir_instrument(score_copy)

    # MIDI 파일로 저장
    mf = midi.translate.music21ObjectToMidiFile(score_copy)
    mf.open(str(output_path), 'wb')
    mf.write()
    mf.close()

    return output_path


def export_parts_midi(
    musicxml_dir: str | Path,
    output_dir: str | Path,
    tempo_bpm: Optional[int] = None
) -> Dict[str, Path]:
    """
    디렉토리 내 모든 MusicXML 파일을 MIDI로 변환

    Args:
        musicxml_dir: MusicXML 파일 디렉토리
        output_dir: MIDI 출력 디렉토리
        tempo_bpm: 템포 (None이면 원본 사용)

    Returns:
        파트명 → MIDI 파일 경로 딕셔너리
    """
    from music21 import converter

    musicxml_dir = Path(musicxml_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for xml_file in sorted(musicxml_dir.glob("*.musicxml")):
        part_name = xml_file.stem
        midi_path = output_dir / f"{part_name}.mid"

        print(f"  변환 중: {xml_file.name} → {midi_path.name}")

        score = converter.parse(str(xml_file))
        export_midi(score, midi_path, tempo_bpm=tempo_bpm)

        results[part_name] = midi_path

    return results


def create_combined_midi(
    part_midis: Dict[str, Path],
    output_path: str | Path,
    highlight_part: Optional[str] = None,
    highlight_volume: int = 100,
    other_volume: int = 40
) -> Path:
    """
    여러 파트 MIDI를 하나로 합치기 (특정 파트 강조 가능)

    Args:
        part_midis: 파트명 → MIDI 경로 딕셔너리
        output_path: 출력 파일 경로
        highlight_part: 강조할 파트명 (None이면 모두 동일 볼륨)
        highlight_volume: 강조 파트 볼륨 (0-127)
        other_volume: 다른 파트 볼륨 (0-127)

    Returns:
        생성된 MIDI 파일 경로
    """
    from music21 import converter

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    combined_score = stream.Score()

    for part_name, midi_path in part_midis.items():
        part_score = converter.parse(str(midi_path))

        for part in part_score.parts:
            part.partName = part_name.capitalize()

            # 볼륨 조절 (velocity)
            if highlight_part:
                target_volume = highlight_volume if part_name == highlight_part else other_volume
                for n in part.flatten().notes:
                    if hasattr(n, 'volume') and n.volume:
                        n.volume.velocity = target_volume

            combined_score.append(part)

    export_midi(combined_score, output_path, use_choir_sound=True)

    return output_path


if __name__ == "__main__":
    import sys
    from music21 import converter

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])

        if input_path.is_dir():
            # 디렉토리: 모든 MusicXML → MIDI
            output_dir = input_path.parent / "midi"
            results = export_parts_midi(input_path, output_dir)
            print(f"\n{len(results)}개 MIDI 파일 생성됨")
        else:
            # 단일 파일
            score = converter.parse(str(input_path))
            output_path = input_path.with_suffix('.mid')
            export_midi(score, output_path)
            print(f"MIDI 저장됨: {output_path}")
