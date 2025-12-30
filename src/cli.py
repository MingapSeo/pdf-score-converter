#!/usr/bin/env python3
"""PDF Score Converter CLI

PDF 합창 악보를 각 성부(SATB)별로 분리하고 MIDI/음원으로 변환하는 CLI 도구
"""

import click
from pathlib import Path
from typing import Optional, List


@click.group()
@click.version_option(version="0.1.0", prog_name="pdf-score-converter")
def cli():
    """PDF 합창 악보 변환 도구

    PDF 악보를 각 성부(SATB)별로 분리하고 MIDI/WAV 음원으로 변환합니다.
    """
    pass


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="출력 디렉토리 (기본: PDF와 같은 위치)")
@click.option("--midi/--no-midi", default=True, help="MIDI 파일 생성")
@click.option("--audio/--no-audio", default=True, help="오디오 파일 생성")
@click.option("--pdf/--no-pdf", "export_pdf", default=True, help="성부별 PDF 생성")
@click.option("--format", "audio_format", type=click.Choice(["wav", "mp3"]),
              default="wav", help="오디오 형식")
@click.option("--dpi", default=200, help="PDF 변환 해상도 (기본: 200)")
@click.option("--tempo", type=int, help="템포 BPM (기본: 원본 유지)")
def convert(
    pdf_path: str,
    output_dir: Optional[str],
    midi: bool,
    audio: bool,
    export_pdf: bool,
    audio_format: str,
    dpi: int,
    tempo: Optional[int]
):
    """PDF 악보를 성부별 MIDI/오디오/PDF로 변환

    전체 파이프라인: PDF → 이미지 → OMR → MusicXML → 성부 분리 → MIDI/오디오/PDF
    """
    from src.omr import recognize_score, OMR_ENGINE
    from src.converter import parse_musicxml, export_parts_midi
    from src.converter.part_splitter import split_satb
    from src.audio import render_parts_audio
    from src.pdf import export_parts_pdf

    pdf_path = Path(pdf_path)

    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_output"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"\n{'='*60}")
    click.echo(f"PDF Score Converter")
    click.echo(f"{'='*60}")
    click.echo(f"입력: {pdf_path}")
    click.echo(f"출력: {output_dir}")
    click.echo(f"{'='*60}\n")

    # 1단계: PDF → MusicXML (OMR)
    click.echo(f"[1/5] PDF 악보 인식 (OMR: {OMR_ENGINE})...")
    try:
        musicxml_paths = recognize_score(pdf_path, output_dir, dpi=dpi)
        click.echo(f"      ✓ {len(musicxml_paths)}개 페이지 인식 완료\n")
    except Exception as e:
        click.echo(f"      ✗ OMR 실패: {e}", err=True)
        return

    if not musicxml_paths:
        click.echo("      ✗ 인식된 악보가 없습니다.", err=True)
        return

    # 2단계: 성부 분리
    click.echo("[2/5] 성부 분리 (SATB)...")
    parts_dir = output_dir / "parts"
    all_parts = {}

    for mxml_path in musicxml_paths:
        try:
            score = parse_musicxml(mxml_path)
            parts = split_satb(score, parts_dir)
            all_parts.update(parts)
        except Exception as e:
            click.echo(f"      ✗ 성부 분리 실패 ({mxml_path.name}): {e}", err=True)

    click.echo(f"      ✓ {len(all_parts)}개 성부 분리 완료\n")

    # 3단계: MIDI 생성
    if midi:
        click.echo("[3/5] MIDI 생성...")
        midi_dir = output_dir / "midi"
        try:
            midi_results = export_parts_midi(parts_dir, midi_dir, tempo_bpm=tempo)
            click.echo(f"      ✓ {len(midi_results)}개 MIDI 생성 완료\n")
        except Exception as e:
            click.echo(f"      ✗ MIDI 생성 실패: {e}", err=True)
            midi_results = {}
    else:
        click.echo("[3/5] MIDI 생성 건너뜀\n")
        midi_results = {}

    # 4단계: 오디오 렌더링
    if audio and midi_results:
        click.echo(f"[4/5] 오디오 렌더링 ({audio_format.upper()})...")
        audio_dir = output_dir / "audio"
        try:
            audio_results = render_parts_audio(midi_dir, audio_dir, format=audio_format)
            click.echo(f"      ✓ {len(audio_results)}개 오디오 생성 완료\n")
        except Exception as e:
            click.echo(f"      ✗ 오디오 생성 실패: {e}", err=True)
            audio_results = {}
    else:
        click.echo("[4/5] 오디오 렌더링 건너뜀\n")
        audio_results = {}

    # 5단계: 성부별 PDF 생성
    if export_pdf:
        click.echo("[5/5] 성부별 PDF 생성...")
        pdf_output_dir = output_dir / "pdf"
        try:
            pdf_results = export_parts_pdf(parts_dir, pdf_output_dir)
            click.echo(f"      ✓ {len(pdf_results)}개 PDF 생성 완료\n")
        except Exception as e:
            click.echo(f"      ✗ PDF 생성 실패: {e}", err=True)
            pdf_results = {}
    else:
        click.echo("[5/5] PDF 생성 건너뜀\n")
        pdf_results = {}

    # 결과 요약
    click.echo(f"{'='*60}")
    click.echo("변환 완료!")
    click.echo(f"{'='*60}")
    click.echo(f"출력 디렉토리: {output_dir}")
    click.echo(f"  - parts/    : {len(all_parts)}개 MusicXML")
    if midi_results:
        click.echo(f"  - midi/     : {len(midi_results)}개 MIDI")
    if audio_results:
        click.echo(f"  - audio/    : {len(audio_results)}개 {audio_format.upper()}")
    if pdf_results:
        click.echo(f"  - pdf/      : {len(pdf_results)}개 PDF")
    click.echo(f"{'='*60}\n")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--dpi", default=200, help="PDF 변환 해상도")
def analyze(pdf_path: str, dpi: int):
    """PDF 악보 구조 분석 (OMR 결과 미리보기)

    악보를 인식하고 파트 구조를 분석하여 표시합니다.
    """
    from src.omr import recognize_score
    from src.converter import parse_musicxml, get_score_info
    from src.converter.musicxml_parser import print_score_info

    pdf_path = Path(pdf_path)
    output_dir = Path("/tmp") / f"analyze_{pdf_path.stem}"

    click.echo(f"\n악보 분석 중: {pdf_path.name}\n")

    # OMR 실행
    click.echo("1. OMR 인식 중...")
    musicxml_paths = recognize_score(pdf_path, output_dir, dpi=dpi)

    if not musicxml_paths:
        click.echo("   인식 실패", err=True)
        return

    # 각 페이지 분석
    for i, mxml_path in enumerate(musicxml_paths, start=1):
        click.echo(f"\n--- 페이지 {i} ---")
        score = parse_musicxml(mxml_path)
        print_score_info(score)


@cli.command()
@click.argument("musicxml_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="출력 디렉토리")
def split(musicxml_path: str, output_dir: Optional[str]):
    """MusicXML 파일을 성부별로 분리

    이미 MusicXML 파일이 있는 경우 직접 성부 분리만 수행합니다.
    """
    from src.converter import parse_musicxml
    from src.converter.part_splitter import split_satb

    musicxml_path = Path(musicxml_path)

    if output_dir is None:
        output_dir = musicxml_path.parent / "parts"
    else:
        output_dir = Path(output_dir)

    click.echo(f"\n성부 분리 중: {musicxml_path.name}\n")

    score = parse_musicxml(musicxml_path)
    results = split_satb(score, output_dir)

    click.echo(f"\n✓ {len(results)}개 성부 분리 완료")
    click.echo(f"  출력: {output_dir}")


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="출력 디렉토리")
@click.option("--format", "audio_format", type=click.Choice(["wav", "mp3"]),
              default="wav", help="오디오 형식")
def render(input_path: str, output_dir: Optional[str], audio_format: str):
    """MIDI 파일을 오디오로 렌더링

    단일 MIDI 파일 또는 디렉토리 내 모든 MIDI 파일을 변환합니다.
    """
    from src.audio import midi_to_audio, render_parts_audio

    input_path = Path(input_path)

    if input_path.is_dir():
        if output_dir is None:
            output_dir = input_path.parent / "audio"
        else:
            output_dir = Path(output_dir)

        click.echo(f"\n오디오 렌더링 중: {input_path}\n")
        results = render_parts_audio(input_path, output_dir, format=audio_format)
        click.echo(f"\n✓ {len(results)}개 오디오 생성 완료")
    else:
        if output_dir is None:
            output_path = input_path.with_suffix(f".{audio_format}")
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}.{audio_format}"

        click.echo(f"\n오디오 렌더링 중: {input_path.name}\n")
        midi_to_audio(input_path, output_path)
        click.echo(f"\n✓ 저장됨: {output_path}")


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="출력 디렉토리")
def export_pdf(input_path: str, output_dir: Optional[str]):
    """MusicXML 파일을 PDF로 변환

    단일 MusicXML 파일 또는 디렉토리 내 모든 MusicXML 파일을 PDF로 변환합니다.
    """
    from src.pdf import musicxml_to_pdf, export_parts_pdf

    input_path = Path(input_path)

    if input_path.is_dir():
        if output_dir is None:
            output_dir = input_path.parent / "pdf"
        else:
            output_dir = Path(output_dir)

        click.echo(f"\nPDF 생성 중: {input_path}\n")
        results = export_parts_pdf(input_path, output_dir)
        click.echo(f"\n✓ {len(results)}개 PDF 생성 완료")
        click.echo(f"  출력: {output_dir}")
    else:
        if output_dir is None:
            output_path = input_path.with_suffix(".pdf")
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}.pdf"

        click.echo(f"\nPDF 생성 중: {input_path.name}\n")
        musicxml_to_pdf(input_path, output_path)
        click.echo(f"\n✓ 저장됨: {output_path}")


def main():
    """CLI 진입점"""
    cli()


if __name__ == "__main__":
    main()
