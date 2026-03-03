#!/usr/bin/env python3
"""Create, edit, and analyze MIDI files.

Usage:
    python midi_tools.py info <file.mid>                       # Analyze MIDI file
    python midi_tools.py chords <key> <progression> -o out.mid # Generate chord progression
    python midi_tools.py drums <pattern> --bpm 90 -o out.mid   # Generate drum pattern
    python midi_tools.py scale <root> <type>                   # Show scale notes
    python midi_tools.py transpose <file.mid> <semitones> -o out.mid  # Transpose MIDI
"""

import sys
import argparse
from pathlib import Path

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

# MIDI note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Scale patterns (intervals in semitones)
SCALES = {
    'major':            [0, 2, 4, 5, 7, 9, 11],
    'minor':            [0, 2, 3, 5, 7, 8, 10],
    'dorian':           [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':       [0, 2, 4, 5, 7, 9, 10],
    'pentatonic':       [0, 2, 4, 7, 9],
    'minor_pentatonic': [0, 3, 5, 7, 10],
    'blues':            [0, 3, 5, 6, 7, 10],
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor':    [0, 2, 3, 5, 7, 9, 11],
    'phrygian':         [0, 1, 3, 5, 7, 8, 10],
    'lydian':           [0, 2, 4, 6, 7, 9, 11],
    'locrian':          [0, 1, 3, 5, 6, 8, 10],
}

# Chord patterns (intervals from root)
CHORDS = {
    'maj':   [0, 4, 7],
    'min':   [0, 3, 7],
    'dim':   [0, 3, 6],
    'aug':   [0, 4, 8],
    '7':     [0, 4, 7, 10],
    'maj7':  [0, 4, 7, 11],
    'min7':  [0, 3, 7, 10],
    'dim7':  [0, 3, 6, 9],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],
    '9':     [0, 4, 7, 10, 14],
    'add9':  [0, 4, 7, 14],
}

# Common drum kit GM mapping
DRUM_MAP = {
    'kick': 36, 'snare': 38, 'rim': 37,
    'hat': 42, 'hat_open': 46, 'hat_pedal': 44,
    'crash': 49, 'ride': 51, 'ride_bell': 53,
    'tom_hi': 50, 'tom_mid': 47, 'tom_lo': 45, 'tom_floor': 43,
    'clap': 39, 'cowbell': 56, 'tambourine': 54,
}

# Preset drum patterns (16-step, 1 = hit, 0 = rest)
DRUM_PATTERNS = {
    'boom_bap': {
        'kick':  [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],
        'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        'hat':   [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
    'trap': {
        'kick':  [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,0],
        'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        'hat':   [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],
    },
    'four_on_floor': {
        'kick':  [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        'hat':   [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
    'reggae': {
        'kick':  [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0],
        'snare': [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],
        'hat':   [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
        'rim':   [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,1],
    },
    'half_time': {
        'kick':  [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
        'hat':   [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
}


def note_to_midi(note_str: str) -> int:
    """Convert note string (e.g., 'C4', 'F#3') to MIDI number."""
    note_str = note_str.strip()
    if note_str[-1].isdigit():
        octave = int(note_str[-1])
        name = note_str[:-1].upper()
    else:
        octave = 4
        name = note_str.upper()
    return NOTE_NAMES.index(name) + (octave + 1) * 12


def midi_to_note(midi_num: int) -> str:
    """Convert MIDI number to note string."""
    octave = (midi_num // 12) - 1
    name = NOTE_NAMES[midi_num % 12]
    return f"{name}{octave}"


def get_scale_notes(root: str, scale_type: str, octave: int = 4) -> list:
    """Get MIDI note numbers for a scale."""
    root_midi = note_to_midi(f"{root}{octave}")
    intervals = SCALES.get(scale_type, SCALES['major'])
    return [root_midi + i for i in intervals]


def analyze_midi(filepath: str) -> dict:
    """Analyze a MIDI file."""
    mid = MidiFile(filepath)

    info = {
        'file': Path(filepath).name,
        'type': mid.type,
        'ticks_per_beat': mid.ticks_per_beat,
        'duration_seconds': round(mid.length, 1),
        'tracks': [],
    }

    for i, track in enumerate(mid.tracks):
        notes = [msg for msg in track if msg.type == 'note_on' and msg.velocity > 0]
        track_info = {
            'index': i,
            'name': track.name or f'Track {i}',
            'note_count': len(notes),
            'messages': len(track),
        }

        if notes:
            pitches = [msg.note for msg in notes]
            track_info['lowest_note'] = midi_to_note(min(pitches))
            track_info['highest_note'] = midi_to_note(max(pitches))
            track_info['velocity_range'] = f"{min(msg.velocity for msg in notes)}-{max(msg.velocity for msg in notes)}"

        for msg in track:
            if msg.type == 'set_tempo':
                info['bpm'] = round(mido.tempo2bpm(msg.tempo), 1)
            elif msg.type == 'time_signature':
                info['time_signature'] = f"{msg.numerator}/{msg.denominator}"

        info['tracks'].append(track_info)

    return info


def generate_chord_progression(key: str, progression: str, bpm: int = 120, octave: int = 3) -> MidiFile:
    """Generate a MIDI chord progression.

    progression format: "I-IV-V-I" or "Cmaj-Fmaj-Gmaj-Cmaj"
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    track.append(MetaMessage('track_name', name=f'Chords - {key} {progression}'))

    ticks_per_beat = mid.ticks_per_beat
    chord_length = ticks_per_beat * 4  # 1 bar per chord

    # Parse Roman numeral progression
    root_midi = note_to_midi(f"{key}{octave}")
    scale = SCALES['major']

    numeral_map = {
        'I': (0, 'maj'), 'II': (1, 'min'), 'III': (2, 'min'),
        'IV': (3, 'maj'), 'V': (4, 'maj'), 'VI': (5, 'min'), 'VII': (6, 'dim'),
        'i': (0, 'min'), 'ii': (1, 'dim'), 'iii': (2, 'maj'),
        'iv': (3, 'min'), 'v': (4, 'min'), 'vi': (5, 'maj'), 'vii': (6, 'maj'),
    }

    chords_str = progression.replace(' ', '').split('-')

    for chord_name in chords_str:
        if chord_name.upper() in [k.upper() for k in numeral_map]:
            matched = next(k for k in numeral_map if k.upper() == chord_name.upper())
            degree, quality = numeral_map[matched]
            chord_root = root_midi + scale[degree]
        else:
            # Direct chord name like "Cmaj", "Fmin"
            for q in sorted(CHORDS.keys(), key=len, reverse=True):
                if chord_name.endswith(q):
                    note_name = chord_name[:-len(q)]
                    chord_root = note_to_midi(f"{note_name}{octave}")
                    quality = q
                    break
            else:
                chord_root = note_to_midi(f"{chord_name}{octave}")
                quality = 'maj'

        intervals = CHORDS.get(quality, CHORDS['maj'])
        notes = [chord_root + i for i in intervals]

        # Note on
        for note in notes:
            track.append(Message('note_on', note=note, velocity=80, time=0))

        # Note off
        track.append(Message('note_off', note=notes[0], velocity=0, time=chord_length))
        for note in notes[1:]:
            track.append(Message('note_off', note=note, velocity=0, time=0))

    return mid


def generate_drum_pattern(pattern_name: str, bpm: int = 90, bars: int = 2) -> MidiFile:
    """Generate a MIDI drum pattern."""
    if pattern_name not in DRUM_PATTERNS:
        print(f"Available patterns: {', '.join(DRUM_PATTERNS.keys())}")
        sys.exit(1)

    pattern = DRUM_PATTERNS[pattern_name]
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    track.append(MetaMessage('track_name', name=f'Drums - {pattern_name}'))

    ticks_per_step = mid.ticks_per_beat // 4  # 16th notes
    steps = 16

    for bar in range(bars):
        for step in range(steps):
            hits = []
            for drum_name, hits_pattern in pattern.items():
                if hits_pattern[step % len(hits_pattern)]:
                    hits.append(DRUM_MAP[drum_name])

            if hits:
                for note in hits:
                    track.append(Message('note_on', note=note, velocity=100,
                                        time=ticks_per_step if not hits.index(note) == 0 or step == 0 and bar == 0 else 0))
                    if hits.index(note) == 0 and not (step == 0 and bar == 0):
                        track[-1].time = ticks_per_step

                # Tiny note length then note off
                track.append(Message('note_off', note=hits[0], velocity=0, time=ticks_per_step // 2))
                for note in hits[1:]:
                    track.append(Message('note_off', note=note, velocity=0, time=0))

                # Account for remaining time
                remaining = ticks_per_step - ticks_per_step // 2
                if remaining > 0 and step < steps - 1:
                    pass  # Next note_on will account for it
            else:
                # Rest - add to next event's time
                pass

    return mid


def transpose_midi(filepath: str, semitones: int) -> MidiFile:
    """Transpose all notes in a MIDI file."""
    mid = MidiFile(filepath)

    for track in mid.tracks:
        for msg in track:
            if msg.type in ('note_on', 'note_off'):
                msg.note = max(0, min(127, msg.note + semitones))

    return mid


def print_midi_info(info: dict):
    """Pretty-print MIDI analysis."""
    print(f"\n{'='*50}")
    print(f"  {info['file']}")
    print(f"{'='*50}")
    print(f"  Type: {info['type']}  |  Duration: {info['duration_seconds']}s")
    if 'bpm' in info:
        print(f"  BPM: {info['bpm']}")
    if 'time_signature' in info:
        print(f"  Time Sig: {info['time_signature']}")
    print(f"  Tracks: {len(info['tracks'])}")

    for t in info['tracks']:
        notes_str = f", {t['note_count']} notes" if t['note_count'] else ""
        range_str = f" ({t.get('lowest_note', '')}-{t.get('highest_note', '')})" if t.get('lowest_note') else ""
        print(f"    {t['index']}. {t['name']}{notes_str}{range_str}")
    print()


def main():
    parser = argparse.ArgumentParser(description='MIDI tools for music production')
    subparsers = parser.add_subparsers(dest='command')

    info_p = subparsers.add_parser('info', help='Analyze MIDI file')
    info_p.add_argument('file', help='MIDI file path')

    chord_p = subparsers.add_parser('chords', help='Generate chord progression MIDI')
    chord_p.add_argument('key', help='Root key (e.g., C, F#, Bb)')
    chord_p.add_argument('progression', help='Chord progression (e.g., "I-IV-V-I")')
    chord_p.add_argument('--bpm', type=int, default=120, help='Tempo (default: 120)')
    chord_p.add_argument('--octave', type=int, default=3, help='Base octave (default: 3)')
    chord_p.add_argument('-o', '--output', required=True, help='Output MIDI file')

    drum_p = subparsers.add_parser('drums', help='Generate drum pattern MIDI')
    drum_p.add_argument('pattern', help=f'Pattern: {", ".join(DRUM_PATTERNS.keys())}')
    drum_p.add_argument('--bpm', type=int, default=90, help='Tempo (default: 90)')
    drum_p.add_argument('--bars', type=int, default=2, help='Number of bars (default: 2)')
    drum_p.add_argument('-o', '--output', required=True, help='Output MIDI file')

    scale_p = subparsers.add_parser('scale', help='Show scale notes')
    scale_p.add_argument('root', help='Root note (e.g., C, F#)')
    scale_p.add_argument('type', nargs='?', default='major', help=f'Scale type: {", ".join(SCALES.keys())}')
    scale_p.add_argument('--octave', type=int, default=4, help='Octave (default: 4)')

    trans_p = subparsers.add_parser('transpose', help='Transpose MIDI file')
    trans_p.add_argument('file', help='Input MIDI file')
    trans_p.add_argument('semitones', type=int, help='Semitones to transpose (+ or -)')
    trans_p.add_argument('-o', '--output', required=True, help='Output MIDI file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'info':
        info = analyze_midi(args.file)
        print_midi_info(info)

    elif args.command == 'chords':
        mid = generate_chord_progression(args.key, args.progression, args.bpm, args.octave)
        mid.save(args.output)
        print(f"Chord progression saved to {args.output}")

    elif args.command == 'drums':
        mid = generate_drum_pattern(args.pattern, args.bpm, args.bars)
        mid.save(args.output)
        print(f"Drum pattern saved to {args.output}")

    elif args.command == 'scale':
        notes = get_scale_notes(args.root, args.type, args.octave)
        note_names = [midi_to_note(n) for n in notes]
        print(f"\n  {args.root} {args.type}: {' - '.join(note_names)}")
        print(f"  Intervals: {SCALES.get(args.type, SCALES['major'])}\n")

    elif args.command == 'transpose':
        mid = transpose_midi(args.file, args.semitones)
        mid.save(args.output)
        direction = "up" if args.semitones > 0 else "down"
        print(f"Transposed {direction} {abs(args.semitones)} semitones -> {args.output}")


if __name__ == '__main__':
    main()
