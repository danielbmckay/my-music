#!/usr/bin/env python3
"""Generate project summaries and track listings.

Scans the project folder and builds an overview of all sessions,
audio exports, and their relationships.

Usage:
    python project_overview.py                      # Full project overview
    python project_overview.py --album              # Album track listing only
    python project_overview.py --exports            # Audio exports inventory
    python project_overview.py --json -o report.json  # Export as JSON
"""

import sys
import json
import gzip
import xml.etree.ElementTree as ET
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_DIR = Path(__file__).parent.parent / "Free Style (LP) Project"
AUDIO_DIR = Path(__file__).parent.parent / "Audio Files"


def parse_als_quick(filepath: Path) -> dict:
    """Quick parse of ALS file for overview data."""
    try:
        with gzip.open(str(filepath), 'rb') as f:
            xml_data = f.read()
        root = ET.fromstring(xml_data)

        tempo_el = root.find('.//Tempo/Manual')
        tempo = float(tempo_el.get('Value', 0)) if tempo_el is not None else 0

        audio_tracks = len(root.findall('.//AudioTrack'))
        midi_tracks = len(root.findall('.//MidiTrack'))

        return {
            'tempo': round(tempo, 1),
            'audio_tracks': audio_tracks,
            'midi_tracks': midi_tracks,
            'total_tracks': audio_tracks + midi_tracks,
        }
    except Exception:
        return {'tempo': 0, 'audio_tracks': 0, 'midi_tracks': 0, 'total_tracks': 0}


def get_album_tracks(project_dir: Path) -> list:
    """Find numbered album tracks (e.g., '1-Title [Sample].als')."""
    tracks = []
    for f in sorted(project_dir.glob('*.als')):
        name = f.stem
        if name[0].isdigit() and '-' in name:
            parts = name.split('-', 1)
            track_num = parts[0]
            rest = parts[1]
            title = rest.split('[')[0].strip() if '[' in rest else rest
            sample = rest.split('[')[1].rstrip(']') if '[' in rest else None

            tracks.append({
                'number': int(track_num),
                'title': title,
                'sample_source': sample,
                'filename': f.name,
                'size_kb': round(f.stat().st_size / 1024, 1),
            })
    return sorted(tracks, key=lambda t: t['number'])


def get_all_sessions(project_dir: Path) -> dict:
    """Categorize all ALS files in the project."""
    album_tracks = []
    working_sessions = []
    alternates = []

    for f in sorted(project_dir.glob('*.als')):
        name = f.stem
        info = {
            'title': name,
            'filename': f.name,
            'size_kb': round(f.stat().st_size / 1024, 1),
            'modified': f.stat().st_mtime,
        }

        if name[0].isdigit() and '-' in name:
            album_tracks.append(info)
        elif any(tag in name.lower() for tag in ['alternate', 'acoustic', 'remix', 'remaster', 'reggae', 'electric']):
            alternates.append(info)
        else:
            working_sessions.append(info)

    return {
        'album_tracks': album_tracks,
        'working_sessions': working_sessions,
        'alternates': alternates,
    }


def get_audio_exports(audio_dir: Path) -> dict:
    """Catalog all exported audio files."""
    exports = defaultdict(list)

    for f in sorted(audio_dir.glob('*')):
        if f.suffix.lower() in ('.aif', '.aiff', '.wav', '.mp3', '.flac'):
            name = f.stem
            base_name = name.split('(')[0].strip()
            variant = name.split('(')[1].rstrip(')') if '(' in name else 'master'

            exports[base_name].append({
                'variant': variant,
                'filename': f.name,
                'size_mb': round(f.stat().st_size / (1024 * 1024), 2),
            })

    return dict(exports)


def print_album_listing(tracks: list):
    """Print formatted album track listing."""
    print(f"\n{'='*60}")
    print(f"  FREE STYLE (LP) - Track Listing")
    print(f"{'='*60}\n")

    for t in tracks:
        sample = f"  [{t['sample_source']}]" if t['sample_source'] else ""
        print(f"  {t['number']:2d}. {t['title']}{sample}")
    print(f"\n  Total: {len(tracks)} tracks\n")


def print_overview(sessions: dict, exports: dict):
    """Print full project overview."""
    album = sessions['album_tracks']
    working = sessions['working_sessions']
    alts = sessions['alternates']

    total = len(album) + len(working) + len(alts)

    print(f"\n{'='*60}")
    print(f"  PROJECT OVERVIEW")
    print(f"{'='*60}")
    print(f"\n  Sessions: {total} total")
    print(f"    Album tracks:      {len(album)}")
    print(f"    Working sessions:  {len(working)}")
    print(f"    Alternate versions:{len(alts)}")
    print(f"\n  Audio Exports: {sum(len(v) for v in exports.values())} files")
    print(f"    Unique songs: {len(exports)}")

    # Songs with most variants
    multi = [(k, v) for k, v in exports.items() if len(v) > 1]
    if multi:
        print(f"\n  Songs with multiple exports:")
        for name, variants in sorted(multi, key=lambda x: len(x[1]), reverse=True)[:10]:
            variant_names = [v['variant'] for v in variants]
            print(f"    {name}: {', '.join(variant_names)}")

    print(f"\n  Recent working sessions:")
    for s in sorted(working, key=lambda x: x['modified'], reverse=True)[:10]:
        print(f"    {s['title']}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Project overview generator')
    parser.add_argument('--album', action='store_true', help='Album track listing only')
    parser.add_argument('--exports', action='store_true', help='Audio exports inventory')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('-o', '--output', help='Save to file')
    parser.add_argument('--project-dir', default=str(PROJECT_DIR), help='Project directory')
    parser.add_argument('--audio-dir', default=str(AUDIO_DIR), help='Audio exports directory')
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    audio_dir = Path(args.audio_dir)

    if args.album:
        tracks = get_album_tracks(project_dir)
        if args.json:
            output = json.dumps(tracks, indent=2)
            if args.output:
                Path(args.output).write_text(output)
            else:
                print(output)
        else:
            print_album_listing(tracks)
        return

    if args.exports:
        exports = get_audio_exports(audio_dir)
        if args.json or args.output:
            output = json.dumps(exports, indent=2)
            if args.output:
                Path(args.output).write_text(output)
                print(f"Export catalog saved to {args.output}")
            else:
                print(output)
        else:
            print(f"\nAudio Exports ({sum(len(v) for v in exports.values())} files):\n")
            for name, variants in sorted(exports.items()):
                for v in variants:
                    print(f"  {v['filename']}  ({v['size_mb']} MB)")
        return

    sessions = get_all_sessions(project_dir)
    exports = get_audio_exports(audio_dir)

    if args.json or args.output:
        data = {'sessions': sessions, 'exports': exports}
        output = json.dumps(data, indent=2, default=str)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Report saved to {args.output}")
        else:
            print(output)
    else:
        print_overview(sessions, exports)


if __name__ == '__main__':
    main()
