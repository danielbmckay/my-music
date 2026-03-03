#!/usr/bin/env python3
"""Restructure .md frontmatter to per-sample format.

Converts single key/bpm fields to a samples array that supports
multi-beat freestyle tracks.

Usage:
    python restructure_frontmatter.py --dry-run    # Preview changes
    python restructure_frontmatter.py               # Apply changes
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Known sample sources from Ableton LP session names
# Format: track_title -> list of {name, artist}
KNOWN_SAMPLES = {
    # '89 Vision self-titled album (from numbered LP sessions)
    "The Sea": [{"name": "Xxplosive", "artist": "Dr. Dre"}],
    "It Hurts": [{"name": "Scarlet Begonias (Rarities)", "artist": "Sublime"}],
    "Starfighter": [{"name": "Bang Bang / Still D.R.E.", "artist": "Dr. Dre"}],
    "Muzak": [{"name": "The Message", "artist": "Dr. Dre"}],
    "My Baby": [{"name": "The Message", "artist": "Dr. Dre"}],
    "The Beginning": [{"name": "Like A Fire", "artist": "Atmosphere"}],
    "The Way": [{"name": "Big Ego's", "artist": "Dr. Dre"}],
    "'89 Vision": [{"name": "The Message", "artist": "Dr. Dre"}],
    # Free Style album — The Words shares beat with The Way
    "The Words": [{"name": "Big Ego's", "artist": "Dr. Dre"}],
    # Bird's Eye medleys (multi-sample tracks)
    "The Way To The Sea": [
        {"name": "Big Ego's", "artist": "Dr. Dre"},
        {"name": "Xxplosive", "artist": "Dr. Dre"},
    ],
    "The Way to The Sea": [
        {"name": "Big Ego's", "artist": "Dr. Dre"},
        {"name": "Xxplosive", "artist": "Dr. Dre"},
    ],
    "Muzak, My Baby": [{"name": "The Message", "artist": "Dr. Dre"}],
    "The Starfighter's Satellite (feat. Luca The Legacy)": [
        {"name": "Bang Bang / Still D.R.E.", "artist": "Dr. Dre"},
    ],
    # Reggae version uses same beat
    "'89 Vision (Reggae)": [{"name": "The Message", "artist": "Dr. Dre"}],
}

# Tracks that share a beat with another (from ALS parenthetical names)
# "4-Muzak (My Baby)" = Muzak and My Baby on same beat
# "6-The Way (The Words)" = The Way and The Words on same beat
SHARED_BEATS = {
    "Muzak": "My Baby",
    "My Baby": "Muzak",
    "The Way": "The Words",
    "The Words": "The Way",
}


def parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text. Returns (fields_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    yaml_block = text[3:end].strip()
    body = text[end + 3:].lstrip("\n")

    fields = {}
    current_key = None
    for line in yaml_block.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        # Check for key: value
        m = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            # Remove surrounding quotes
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fields[key] = val
            current_key = key
        elif current_key == "sample" and line.startswith("  "):
            # Multi-line sample field (unlikely but handle)
            fields[current_key] += " " + line.strip()

    return fields, body


def build_samples_yaml(samples, key=None, bpm=None):
    """Build YAML samples array."""
    lines = ["samples:"]
    if samples:
        for i, s in enumerate(samples):
            lines.append(f'  - name: "{s["name"]}"')
            if "artist" in s:
                lines.append(f'    artist: "{s["artist"]}"')
            # Assign key/bpm to first sample if we only have one set of values
            if i == 0 and key:
                lines.append(f'    key: "{key}"')
            if i == 0 and bpm:
                lines.append(f"    bpm: {bpm}")
    else:
        # Unknown sample source — just key/bpm
        lines.append("  - key: \"" + (key or "?") + "\"")
        if bpm:
            lines.append(f"    bpm: {bpm}")
    return "\n".join(lines)


def build_frontmatter(fields, samples_yaml=None):
    """Reconstruct frontmatter YAML string."""
    lines = ["---"]

    # Always put artist and album first
    if "artist" in fields:
        val = fields["artist"]
        if "'" in val or " " in val:
            lines.append(f'artist: "{val}"')
        else:
            lines.append(f"artist: {val}")
    if "album" in fields:
        val = fields["album"]
        if "'" in val or " " in val:
            lines.append(f'album: "{val}"')
        else:
            lines.append(f"album: {val}")

    # Type field (AA Audible)
    if "type" in fields:
        lines.append(f'type: "{fields["type"]}"')

    # Producer
    if "producer" in fields:
        lines.append(f"producer: {fields['producer']}")

    # Track number
    if "track" in fields:
        lines.append(f"track: {fields['track']}")

    # Scripture (AA Audible)
    if "scripture" in fields:
        lines.append(f'scripture: "{fields["scripture"]}"')

    # Samples array (replaces key/bpm/sample)
    if samples_yaml:
        lines.append(samples_yaml)

    # Note field
    if "note" in fields:
        lines.append(f'note: "{fields["note"]}"')

    lines.append("---")
    return "\n".join(lines)


def get_track_title(filepath):
    """Extract track title from filename."""
    return filepath.stem


def lookup_known_samples(title):
    """Case-insensitive lookup in KNOWN_SAMPLES."""
    # Try exact match first
    if title in KNOWN_SAMPLES:
        return KNOWN_SAMPLES[title]
    # Try case-insensitive
    title_lower = title.lower()
    for k, v in KNOWN_SAMPLES.items():
        if k.lower() == title_lower:
            return v
    return None


def should_restructure(fields, filepath):
    """Determine if this file needs sample restructuring."""
    # Skip AA Audible (spoken word, no samples)
    if "AA Audible" in str(filepath):
        return False
    # Only restructure if we have key or bpm or sample data
    return "key" in fields or "bpm" in fields or "sample" in fields


def restructure_file(filepath, dry_run=True):
    """Restructure a single .md file's frontmatter."""
    text = filepath.read_text()
    fields, body = parse_frontmatter(text)

    if not fields:
        return None

    if not should_restructure(fields, filepath):
        return None

    title = get_track_title(filepath)
    key = fields.get("key")
    bpm = fields.get("bpm")

    # Check for known sample sources
    known = lookup_known_samples(title)

    # Also check if there's an existing sample field (like in Starfighter.md)
    existing_sample = fields.get("sample")
    if existing_sample and not known:
        # Parse "Sample Name, Artist" format
        parts = existing_sample.rsplit(",", 1)
        if len(parts) == 2:
            known = [{"name": parts[0].strip(), "artist": parts[1].strip()}]
        else:
            known = [{"name": existing_sample}]

    # Build samples YAML
    samples_yaml = build_samples_yaml(known, key, bpm)

    # Build new frontmatter (without key/bpm/sample — those are now in samples)
    new_fm = build_frontmatter(fields, samples_yaml)
    new_text = new_fm + "\n\n" + body if body else new_fm + "\n"

    if new_text == text:
        return None

    if dry_run:
        return {"file": str(filepath.relative_to(BASE)), "old": text[:300], "new": new_text[:300]}
    else:
        filepath.write_text(new_text)
        return {"file": str(filepath.relative_to(BASE))}


def main():
    dry_run = "--dry-run" in sys.argv

    # Find all .md files in 89 Vision/ and AA Audible/
    md_files = sorted(
        list(BASE.glob("89 Vision/**/*.md")) +
        list(BASE.glob("AA Audible/**/*.md"))
    )

    print(f"Found {len(md_files)} .md files")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLYING CHANGES'}\n")

    changed = []
    skipped = 0

    for f in md_files:
        result = restructure_file(f, dry_run=dry_run)
        if result:
            changed.append(result)
            rel = result["file"]
            if dry_run:
                print(f"  CHANGE: {rel}")
                # Show before/after frontmatter
                old_fm = result["old"].split("---")[1] if "---" in result["old"] else ""
                new_fm = result["new"].split("---")[1] if "---" in result["new"] else ""
                print(f"    key/bpm → samples array")
            else:
                print(f"  UPDATED: {rel}")
        else:
            skipped += 1

    print(f"\n{'Would change' if dry_run else 'Changed'}: {len(changed)} files")
    print(f"Skipped: {skipped} files (AA Audible or no key/bpm)")

    if dry_run and changed:
        print(f"\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
