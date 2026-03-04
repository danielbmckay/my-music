#!/usr/bin/env python3
"""Parse and inspect Ableton Live Set (.als) files.

ALS files are gzip-compressed XML. This tool decompresses and parses them
to extract session info like tempo, time signature, tracks, clips, and devices.

Usage:
    python als_parser.py <file.als>                    # Full summary
    python als_parser.py <file.als> --tracks           # List all tracks
    python als_parser.py <file.als> --tempo            # Show tempo only
    python als_parser.py <file.als> --xml              # Dump raw XML
    python als_parser.py <file.als> --xml -o out.xml   # Save XML to file
"""

import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import json


def decompress_als(filepath: str) -> bytes:
    """Decompress an ALS file and return the raw XML bytes."""
    with gzip.open(filepath, 'rb') as f:
        return f.read()


def parse_als(filepath: str) -> ET.Element:
    """Parse an ALS file and return the XML root element."""
    xml_data = decompress_als(filepath)
    return ET.fromstring(xml_data)


def get_tempo(root: ET.Element) -> float:
    """Extract the master tempo from the session."""
    tempo_el = root.find('.//Tempo/Manual')
    if tempo_el is not None:
        return float(tempo_el.get('Value', 120))
    return 120.0


def get_time_signature(root: ET.Element) -> str:
    """Extract the time signature."""
    num = root.find('.//TimeSignature/TimeSignatures/RemoteableTimeSignature/Numerator')
    den = root.find('.//TimeSignature/TimeSignatures/RemoteableTimeSignature/Denominator')
    if num is not None and den is not None:
        return f"{num.get('Value', '4')}/{den.get('Value', '4')}"
    return "4/4"


def get_tracks(root: ET.Element) -> list:
    """Extract all tracks with their names and types."""
    tracks = []
    track_types = {
        'AudioTrack': 'Audio',
        'MidiTrack': 'MIDI',
        'ReturnTrack': 'Return',
        'GroupTrack': 'Group',
    }

    for tag, track_type in track_types.items():
        for track in root.findall(f'.//{tag}'):
            name_el = track.find('.//Name/EffectiveName')
            if name_el is None:
                name_el = track.find('.//Name/UserName')
            name = name_el.get('Value', 'Unnamed') if name_el is not None else 'Unnamed'

            frozen = track.find('.//Freeze')
            is_frozen = frozen.get('Value', 'false') == 'true' if frozen is not None else False

            color = track.find('.//Color')
            color_idx = int(color.get('Value', -1)) if color is not None else -1

            tracks.append({
                'name': name,
                'type': track_type,
                'frozen': is_frozen,
                'color_index': color_idx,
            })

    return tracks


def get_master_info(root: ET.Element) -> dict:
    """Extract master track info."""
    master = root.find('.//MasterTrack')
    if master is None:
        return {}

    volume = master.find('.//DeviceChain/Mixer/Volume/Manual')
    return {
        'volume': float(volume.get('Value', 0)) if volume is not None else 0,
    }


def get_scenes(root: ET.Element) -> list:
    """Extract scene names."""
    scenes = []
    for scene in root.findall('.//Scene'):
        name = scene.find('.//Name')
        if name is not None:
            scenes.append(name.get('Value', 'Unnamed'))
    return scenes


def get_clip_count(root: ET.Element) -> dict:
    """Count audio and MIDI clips."""
    audio_clips = len(root.findall('.//AudioClip'))
    midi_clips = len(root.findall('.//MidiClip'))
    return {'audio': audio_clips, 'midi': midi_clips, 'total': audio_clips + midi_clips}


def get_devices(root: ET.Element) -> list:
    """Extract all plugin/device names used in the session."""
    devices = set()

    for plugin in root.findall('.//PluginDesc/VstPluginInfo/PlugName'):
        devices.add(f"VST: {plugin.get('Value', 'Unknown')}")

    for plugin in root.findall('.//PluginDesc/AuPluginInfo/Name'):
        devices.add(f"AU: {plugin.get('Value', 'Unknown')}")

    for plugin in root.findall('.//PluginDesc/Vst3PluginInfo/Name'):
        devices.add(f"VST3: {plugin.get('Value', 'Unknown')}")

    return sorted(devices)


def summarize(filepath: str) -> dict:
    """Generate a full summary of an ALS file."""
    root = parse_als(filepath)
    tracks = get_tracks(root)
    clips = get_clip_count(root)
    devices = get_devices(root)
    scenes = get_scenes(root)

    return {
        'file': Path(filepath).name,
        'tempo': get_tempo(root),
        'time_signature': get_time_signature(root),
        'tracks': {
            'total': len(tracks),
            'audio': sum(1 for t in tracks if t['type'] == 'Audio'),
            'midi': sum(1 for t in tracks if t['type'] == 'MIDI'),
            'return': sum(1 for t in tracks if t['type'] == 'Return'),
            'group': sum(1 for t in tracks if t['type'] == 'Group'),
            'details': tracks,
        },
        'clips': clips,
        'scenes': scenes,
        'devices': devices,
        'master': get_master_info(root),
    }


def print_summary(summary: dict):
    """Pretty-print a session summary."""
    print(f"\n{'='*60}")
    print(f"  {summary['file']}")
    print(f"{'='*60}")
    print(f"  Tempo: {summary['tempo']} BPM")
    print(f"  Time Signature: {summary['time_signature']}")
    print(f"  Tracks: {summary['tracks']['total']} "
          f"({summary['tracks']['audio']} audio, "
          f"{summary['tracks']['midi']} MIDI, "
          f"{summary['tracks']['return']} return, "
          f"{summary['tracks']['group']} group)")
    print(f"  Clips: {summary['clips']['total']} "
          f"({summary['clips']['audio']} audio, {summary['clips']['midi']} MIDI)")

    if summary['scenes']:
        print(f"  Scenes: {len(summary['scenes'])}")

    if summary['devices']:
        print(f"\n  Plugins/Devices ({len(summary['devices'])}):")
        for d in summary['devices']:
            print(f"    - {d}")

    print(f"\n  Track List:")
    for i, t in enumerate(summary['tracks']['details'], 1):
        frozen = " [FROZEN]" if t['frozen'] else ""
        print(f"    {i:2d}. [{t['type']:6s}] {t['name']}{frozen}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Parse Ableton Live Set files')
    parser.add_argument('file', help='Path to .als file')
    parser.add_argument('--tracks', action='store_true', help='List tracks only')
    parser.add_argument('--tempo', action='store_true', help='Show tempo only')
    parser.add_argument('--xml', action='store_true', help='Dump raw XML')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('-o', '--output', help='Save output to file')
    args = parser.parse_args()

    filepath = args.file
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if args.xml:
        xml_data = decompress_als(filepath)
        output = xml_data.decode('utf-8')
        if args.output:
            Path(args.output).write_text(output)
            print(f"XML saved to {args.output}")
        else:
            print(output)
        return

    if args.tempo:
        root = parse_als(filepath)
        print(f"{get_tempo(root)} BPM")
        return

    if args.tracks:
        root = parse_als(filepath)
        for i, t in enumerate(get_tracks(root), 1):
            frozen = " [FROZEN]" if t['frozen'] else ""
            print(f"  {i:2d}. [{t['type']:6s}] {t['name']}{frozen}")
        return

    summary = summarize(filepath)

    if args.json:
        output = json.dumps(summary, indent=2)
        if args.output:
            Path(args.output).write_text(output)
            print(f"JSON saved to {args.output}")
        else:
            print(output)
        return

    print_summary(summary)


if __name__ == '__main__':
    main()
