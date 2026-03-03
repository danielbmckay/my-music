#!/usr/bin/env python3
"""Analyze audio files for BPM, key, loudness, and duration.

Uses essentia for music analysis and ffprobe for metadata.

Usage:
    python audio_info.py <file.aif>              # Full analysis
    python audio_info.py <file.aif> --bpm        # BPM only
    python audio_info.py <file.aif> --key        # Key only
    python audio_info.py <directory> --batch      # Analyze all audio in directory
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path

AUDIO_EXTENSIONS = {'.aif', '.aiff', '.wav', '.mp3', '.flac', '.ogg', '.m4a'}


def get_ffprobe_info(filepath: str) -> dict:
    """Get audio metadata via ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filepath],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'audio'), {})
        fmt = data.get('format', {})
        return {
            'duration_seconds': float(fmt.get('duration', 0)),
            'duration': format_duration(float(fmt.get('duration', 0))),
            'sample_rate': int(stream.get('sample_rate', 0)),
            'channels': int(stream.get('channels', 0)),
            'bit_depth': stream.get('bits_per_raw_sample', stream.get('bits_per_sample', 'N/A')),
            'codec': stream.get('codec_name', 'unknown'),
            'file_size_mb': round(int(fmt.get('size', 0)) / (1024 * 1024), 2),
        }
    except (subprocess.SubprocessError, json.JSONDecodeError, StopIteration):
        return {}


def format_duration(seconds: float) -> str:
    """Format seconds into MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def analyze_with_essentia(filepath: str) -> dict:
    """Analyze audio with essentia for BPM, key, and loudness."""
    try:
        import essentia.standard as es

        audio = es.MonoLoader(filename=filepath, sampleRate=44100)()

        # BPM detection
        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)

        # Key detection
        key_extractor = es.KeyExtractor()
        key, scale, key_strength = key_extractor(audio)

        # Loudness
        loudness = es.Loudness()(audio)
        loudness_momentary = es.LoudnessEBUR128()(audio)
        integrated_loudness = loudness_momentary[0]

        return {
            'bpm': round(bpm, 1),
            'bpm_confidence': round(float(beats_confidence), 2),
            'key': key,
            'scale': scale,
            'key_label': f"{key} {scale}",
            'key_confidence': round(float(key_strength), 2),
            'loudness_lufs': round(float(integrated_loudness), 1),
        }
    except ImportError:
        return {'error': 'essentia not installed - run: pip install essentia-tensorflow'}
    except Exception as e:
        return {'error': str(e)}


def analyze_file(filepath: str) -> dict:
    """Full analysis of an audio file."""
    path = Path(filepath)
    result = {
        'file': path.name,
        'path': str(path),
    }
    result.update(get_ffprobe_info(filepath))
    result.update(analyze_with_essentia(filepath))
    return result


def print_analysis(info: dict):
    """Pretty-print audio analysis."""
    print(f"\n{'='*50}")
    print(f"  {info.get('file', 'Unknown')}")
    print(f"{'='*50}")

    if 'duration' in info:
        print(f"  Duration:    {info['duration']}")
    if 'sample_rate' in info:
        print(f"  Sample Rate: {info['sample_rate']} Hz")
    if 'channels' in info:
        ch = 'Stereo' if info['channels'] == 2 else 'Mono' if info['channels'] == 1 else f"{info['channels']}ch"
        print(f"  Channels:    {ch}")
    if 'bit_depth' in info and info['bit_depth'] != 'N/A':
        print(f"  Bit Depth:   {info['bit_depth']}-bit")
    if 'codec' in info:
        print(f"  Codec:       {info['codec']}")
    if 'file_size_mb' in info:
        print(f"  File Size:   {info['file_size_mb']} MB")

    if 'bpm' in info:
        conf = f" (confidence: {info['bpm_confidence']})" if 'bpm_confidence' in info else ""
        print(f"  BPM:         {info['bpm']}{conf}")
    if 'key_label' in info:
        conf = f" (confidence: {info['key_confidence']})" if 'key_confidence' in info else ""
        print(f"  Key:         {info['key_label']}{conf}")
    if 'loudness_lufs' in info:
        print(f"  Loudness:    {info['loudness_lufs']} LUFS")

    if 'error' in info:
        print(f"  Analysis:    {info['error']}")

    print()


def batch_analyze(directory: str) -> list:
    """Analyze all audio files in a directory."""
    path = Path(directory)
    results = []
    files = sorted(f for f in path.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS)

    print(f"Found {len(files)} audio files in {directory}\n")
    for f in files:
        print(f"  Analyzing: {f.name}...", end='', flush=True)
        info = analyze_file(str(f))
        results.append(info)
        bpm = info.get('bpm', '?')
        key = info.get('key_label', '?')
        dur = info.get('duration', '?')
        print(f"  {dur} | {bpm} BPM | {key}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Analyze audio files')
    parser.add_argument('path', help='Audio file or directory path')
    parser.add_argument('--bpm', action='store_true', help='Show BPM only')
    parser.add_argument('--key', action='store_true', help='Show key only')
    parser.add_argument('--batch', action='store_true', help='Analyze all audio files in directory')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('-o', '--output', help='Save output to file')
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f"Error: Not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if args.batch or Path(args.path).is_dir():
        results = batch_analyze(args.path)
        if args.json or args.output:
            output = json.dumps(results, indent=2)
            if args.output:
                Path(args.output).write_text(output)
                print(f"\nResults saved to {args.output}")
            else:
                print(output)
        return

    info = analyze_file(args.path)

    if args.bpm:
        print(info.get('bpm', 'Unknown'))
        return
    if args.key:
        print(info.get('key_label', 'Unknown'))
        return

    if args.json:
        output = json.dumps(info, indent=2)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Results saved to {args.output}")
        else:
            print(output)
        return

    print_analysis(info)


if __name__ == '__main__':
    main()
