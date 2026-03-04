#!/usr/bin/env python3
"""Identify sample sources in audio files using Shazam recognition.

Extracts a segment from each track and runs it through Shazam to identify
the underlying beat/sample.

Usage:
    python identify_samples.py <file.aif>           # Single file
    python identify_samples.py --unknown             # All unknown tracks
    python identify_samples.py --all                 # All .aif files
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE / "89 Vision"


async def identify_track(filepath, offset=30):
    """Run Shazam recognition on a segment of audio."""
    from shazamio import Shazam

    path = Path(filepath)
    if not path.exists():
        return {"file": path.name, "error": "File not found"}

    # Extract a 15-second segment starting at offset using ffmpeg
    # (skip intro, get into the beat)
    tmp = BASE / "Claude" / f"shazam_tmp_{path.stem}.wav"
    tmp.parent.mkdir(exist_ok=True)

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(path), "-ss", str(offset), "-t", "15",
             "-ar", "44100", "-ac", "1", str(tmp)],
            capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        return {"file": path.name, "error": f"ffmpeg failed: {e.stderr.decode()[:200]}"}

    try:
        shazam = Shazam()
        result = await shazam.recognize(str(tmp))

        if result and "track" in result:
            track = result["track"]
            return {
                "file": path.name,
                "match": True,
                "title": track.get("title", "Unknown"),
                "artist": track.get("subtitle", "Unknown"),
                "album": track.get("sections", [{}])[0].get("metadata", [{}])[0].get("text", "") if track.get("sections") else "",
            }
        else:
            return {"file": path.name, "match": False}
    except Exception as e:
        return {"file": path.name, "error": str(e)}
    finally:
        if tmp.exists():
            tmp.unlink()


async def identify_multiple(files, offset=30):
    """Identify multiple files sequentially (to avoid rate limiting)."""
    results = []
    for f in files:
        print(f"  Analyzing: {f.name}...", end="", flush=True)
        result = await identify_track(str(f), offset)
        if result.get("match"):
            print(f"  MATCH: {result['title']} — {result['artist']}")
        elif result.get("error"):
            print(f"  ERROR: {result['error'][:60]}")
        else:
            print(f"  No match")
        results.append(result)
        # Brief pause to avoid rate limiting
        await asyncio.sleep(1)
    return results


def find_unknown_audio():
    """Find .aif files for tracks classified as 'unknown'."""
    import re
    files = []
    for md in sorted(BASE.glob("89 Vision/**/*.md")):
        text = md.read_text()
        if 'release_type: "unknown"' not in text:
            continue

        # Find matching .aif file
        # Audio files are in a flat directory or alongside the .md
        stem = md.stem
        # Check common locations
        candidates = list(BASE.rglob(f"{stem}.aif"))
        if candidates:
            files.append(candidates[0])
        else:
            print(f"  No .aif found for: {stem}")
    return files


def main():
    if "--unknown" in sys.argv:
        print("Finding unknown tracks...")
        files = find_unknown_audio()
        print(f"Found {len(files)} audio files for unknown tracks\n")
    elif "--all" in sys.argv:
        audio_dir = sys.argv[sys.argv.index("--all") + 1] if len(sys.argv) > sys.argv.index("--all") + 1 else str(BASE)
        files = sorted(Path(audio_dir).glob("*.aif"))
        print(f"Found {len(files)} .aif files\n")
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        files = [Path(sys.argv[1])]
    else:
        print(__doc__)
        return

    offset = 30
    if "--offset" in sys.argv:
        offset = int(sys.argv[sys.argv.index("--offset") + 1])

    results = asyncio.run(identify_multiple(files, offset))

    # Save results
    output = BASE / "Claude" / "shazam_results.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")

    # Summary
    matches = [r for r in results if r.get("match")]
    no_match = [r for r in results if not r.get("match") and not r.get("error")]
    errors = [r for r in results if r.get("error")]

    print(f"\nMatched: {len(matches)}")
    print(f"No match: {len(no_match)}")
    print(f"Errors: {len(errors)}")

    if matches:
        print("\nIdentified samples:")
        for m in matches:
            print(f"  {m['file']:40s} → {m['title']} — {m['artist']}")


if __name__ == "__main__":
    main()
