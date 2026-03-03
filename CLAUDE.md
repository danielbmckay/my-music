# Ableton Music Production Agent

## About This Project

**Artist:** Daniel McKay
**DAW:** Ableton Live
**Primary Project:** Free Style (LP) - a full-length album project
**Audio Format:** AIF (Apple AIFF)

## Project Structure

```
My Music/
├── Free Style (LP) Project/    # Main Ableton project folder (369 .als files)
│   ├── *.als                   # Ableton Live Sets (gzipped XML)
│   ├── *.alc                   # Ableton Live Clips
│   └── Ableton Project Info/   # Ableton metadata
├── Audio Files/                # Exported/bounced audio (142 files, .aif + .asd)
├── SAMPLES/                    # Sample libraries
│   └── Focusrite Samples/      # Focusrite bundled samples
├── tools/                      # Python helper scripts
│   └── *.py                    # ALS parser, sample manager, audio analysis
├── claude-temp/                # Temporary working files (gitignored)
└── .venv/                      # Python virtual environment
```

## Ableton File Formats

| Extension | Format | Description |
|-----------|--------|-------------|
| `.als` | Gzipped XML | Ableton Live Set - full session with tracks, clips, devices |
| `.alc` | Gzipped XML | Ableton Live Clip - individual clip with audio/MIDI + devices |
| `.adg` | Gzipped XML | Ableton Device Group - instrument/effect rack preset |
| `.asd` | Binary | Ableton analysis file (warp markers, transients) - auto-generated |

**Reading ALS/ALC/ADG files:** These are all gzip-compressed XML. Use `tools/als_parser.py` to decompress and parse them. Never modify these files while Ableton has them open.

## Available Tools

### Python Environment
```bash
cd ~/Desktop/My\ Music
source .venv/bin/activate
```

**Installed packages:**
- `mido` - MIDI file reading/writing/manipulation
- `pretty_midi` - High-level MIDI analysis (tempo, key, instrument programs)
- `essentia-tensorflow` - Audio analysis (BPM detection, key estimation, loudness LUFS)
- `soundfile` - Audio file I/O (read/write WAV, AIFF, FLAC)
- `pydub` - Audio manipulation (trim, concat, fade, convert formats)
- `music21` - Music theory (scales, chords, intervals, notation)
- `numpy` - Numerical computing (used by audio libraries)

### Helper Scripts (`tools/`)
- `als_parser.py` - Parse and inspect Ableton Live Set files
- `sample_manager.py` - Organize, tag, and search samples
- `audio_info.py` - Analyze audio files (duration, BPM, key, loudness)
- `midi_tools.py` - Create, edit, and analyze MIDI files
- `project_overview.py` - Generate project summaries and track listings

### System Tools
- `ffmpeg` / `ffprobe` - Audio conversion and metadata extraction
- `osascript` - AppleScript for Ableton automation (launch, transport control)

## What I Can Help With

### Production Workflow
- Parse ALS files to understand session structure (tracks, clips, tempo, time signature)
- Analyze audio files for BPM, key, loudness, duration
- Generate MIDI patterns (drums, basslines, chord progressions)
- Music theory assistance (scales, chord voicings, progressions, modes)
- Arrangement suggestions based on song structure analysis

### File Management
- Organize and rename audio files with consistent naming conventions
- Catalog samples with metadata (BPM, key, type)
- Find unused samples or duplicate audio files
- Generate project inventories and track listings
- Batch rename exports

### Ableton Automation
- Read and analyze ALS project files without opening Ableton
- Extract tempo, time signature, track names, and plugin info from sessions
- Launch Ableton and control basic transport via AppleScript
- Compare versions of the same song across different ALS files

### Mixing & Mastering Guidance
- Suggest EQ, compression, and effects settings
- Analyze frequency content and loudness levels
- Provide mixing reference notes and gain staging advice
- Help with vocal processing chains

## Naming Conventions

**ALS Files (Album Tracks):**
- Album tracks: `[Track#]-[Title] [Sample Source].als`
  - Example: `1-The Sea (My Father) [Xxplosive, Dr. Dre].als`
- Working sessions: `[Title].als`
  - Example: `Above The Clouds.als`
- Alternate versions: `[Title] (Alternate).als` or `[Title] (Acoustic).als`

**Audio Exports:**
- Master: `[Title].aif`
- Instrumental: `[Title] (Instrumental).aif`
- Alternate mix: `[Title] (remastered).aif`
- Raw stems: `[Title] (raw vocals).aif`

## Important Rules

1. **Never modify .als files while Ableton is running** - can corrupt the session
2. **Always back up before batch operations** on audio files
3. **Keep .asd files** alongside their audio - they contain warp/analysis data
4. **Temporary files go in:** `~/Desktop/My Music/claude-temp/`
5. **Audio format preference:** AIF (AIFF) is the primary format used in this project
6. **Python venv:** Always use `.venv` (with dot prefix) for virtual environment