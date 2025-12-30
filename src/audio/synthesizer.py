"""MIDI to Audio 합성 모듈 (FluidSynth 사용)"""

import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional


# 기본 SoundFont 경로들 (우선순위 순)
DEFAULT_SOUNDFONTS = [
    "/opt/homebrew/share/soundfonts/FluidR3_GM.sf2",
    "/opt/homebrew/Cellar/fluid-synth/2.5.2/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2",
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/soundfonts/FluidR3_GM.sf2",
]


def find_soundfont() -> Optional[Path]:
    """
    시스템에서 사용 가능한 SoundFont 찾기

    Returns:
        SoundFont 파일 경로 (없으면 None)
    """
    # 프로젝트 내 SoundFont 확인
    project_sf = Path(__file__).parent.parent.parent / "soundfonts"
    if project_sf.exists():
        for sf in project_sf.glob("*.sf2"):
            return sf

    # 시스템 SoundFont 확인
    for sf_path in DEFAULT_SOUNDFONTS:
        if Path(sf_path).exists():
            return Path(sf_path)

    # Homebrew로 설치된 SoundFont 검색
    homebrew_sf = Path("/opt/homebrew/Cellar/fluid-synth")
    if homebrew_sf.exists():
        for sf in homebrew_sf.rglob("*.sf2"):
            return sf

    return None


def download_soundfont(output_dir: str | Path) -> Path:
    """
    GM SoundFont 다운로드

    Args:
        output_dir: 다운로드 디렉토리

    Returns:
        다운로드된 SoundFont 경로
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sf_path = output_dir / "GeneralUser_GS.sf2"

    if sf_path.exists():
        return sf_path

    # GeneralUser GS SoundFont 다운로드 (무료, 고품질)
    url = "https://github.com/FluidSynth/fluidsynth/releases/download/v2.3.0/GeneralUser_GS.sf2"

    print(f"SoundFont 다운로드 중: {url}")
    subprocess.run(
        ["curl", "-L", "-o", str(sf_path), url],
        check=True
    )

    return sf_path


def midi_to_audio(
    midi_path: str | Path,
    output_path: str | Path,
    soundfont: Optional[str | Path] = None,
    sample_rate: int = 44100,
    gain: float = 1.0
) -> Path:
    """
    MIDI 파일을 오디오 파일로 변환

    Args:
        midi_path: MIDI 파일 경로
        output_path: 출력 오디오 파일 경로 (.wav 또는 .mp3)
        soundfont: SoundFont 파일 경로 (None이면 자동 탐색)
        sample_rate: 샘플레이트 (기본 44100Hz)
        gain: 볼륨 게인 (기본 1.0)

    Returns:
        생성된 오디오 파일 경로
    """
    midi_path = Path(midi_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # SoundFont 찾기
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            # SoundFont 다운로드
            soundfont = download_soundfont(Path(__file__).parent.parent.parent / "soundfonts")

    soundfont = Path(soundfont)
    if not soundfont.exists():
        raise FileNotFoundError(f"SoundFont를 찾을 수 없습니다: {soundfont}")

    # 출력 형식 결정
    output_suffix = output_path.suffix.lower()

    if output_suffix == ".wav":
        # FluidSynth로 직접 WAV 생성
        cmd = [
            "fluidsynth",
            "-ni",  # No shell, non-interactive
            "-g", str(gain),
            "-r", str(sample_rate),
            "-F", str(output_path),
            str(soundfont),
            str(midi_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    elif output_suffix == ".mp3":
        # WAV로 먼저 생성 후 MP3로 변환
        wav_path = output_path.with_suffix('.wav')

        # WAV 생성
        cmd = [
            "fluidsynth",
            "-ni",
            "-g", str(gain),
            "-r", str(sample_rate),
            "-F", str(wav_path),
            str(soundfont),
            str(midi_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        # MP3로 변환 (lame 사용)
        try:
            subprocess.run(
                ["lame", "-b", "192", str(wav_path), str(output_path)],
                check=True,
                capture_output=True
            )
            wav_path.unlink()  # WAV 파일 삭제
        except FileNotFoundError:
            # lame이 없으면 WAV 유지
            print("  경고: lame이 설치되지 않아 WAV로 저장됨")
            output_path = wav_path

    else:
        raise ValueError(f"지원하지 않는 오디오 형식: {output_suffix}")

    return output_path


def render_parts_audio(
    midi_dir: str | Path,
    output_dir: str | Path,
    format: str = "wav",
    soundfont: Optional[str | Path] = None
) -> Dict[str, Path]:
    """
    디렉토리 내 모든 MIDI 파일을 오디오로 변환

    Args:
        midi_dir: MIDI 파일 디렉토리
        output_dir: 오디오 출력 디렉토리
        format: 출력 형식 (wav 또는 mp3)
        soundfont: SoundFont 파일 경로

    Returns:
        파트명 → 오디오 파일 경로 딕셔너리
    """
    midi_dir = Path(midi_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for midi_file in sorted(midi_dir.glob("*.mid")):
        part_name = midi_file.stem
        audio_path = output_dir / f"{part_name}.{format}"

        print(f"  렌더링 중: {midi_file.name} → {audio_path.name}")

        try:
            midi_to_audio(midi_file, audio_path, soundfont=soundfont)
            results[part_name] = audio_path
        except Exception as e:
            print(f"  오류: {e}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])

        if input_path.is_dir():
            # 디렉토리: 모든 MIDI → WAV
            output_dir = input_path.parent / "audio"
            results = render_parts_audio(input_path, output_dir)
            print(f"\n{len(results)}개 오디오 파일 생성됨")
        else:
            # 단일 파일
            output_path = input_path.with_suffix('.wav')
            midi_to_audio(input_path, output_path)
            print(f"오디오 저장됨: {output_path}")
