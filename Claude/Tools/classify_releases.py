#!/usr/bin/env python3
"""Classify tracks by release type for distribution clearance.

Release types:
  original  — Danny's own lyrics + own beat. Free to release.
  cover     — Performing someone else's song. Needs mechanical license.
  mixtape   — Original vocals over someone else's beat. Free release only.
  collab    — Produced with another artist. Needs collaboration agreement.
  scripture — Spoken word scripture/prayer. Check translation copyright.
  unknown   — Not yet classified. Needs manual review.

Usage:
    python classify_releases.py --dry-run    # Preview classifications
    python classify_releases.py               # Apply to .md files
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# ── Classification Rules ──

# Tracks with known samples (from ALS LP session names) → "sample"
SAMPLED_TRACKS = {
    "The Sea", "It Hurts", "Starfighter", "Muzak", "My Baby",
    "The Beginning", "The Way", "'89 Vision", "'89 Vision (Reggae)",
    "The Words", "Run Away", "Free Style",
    # Bird's Eye medleys (built from sampled tracks)
    "The Way To The Sea", "The Way to The Sea",
    "Muzak, My Baby",
    "The Starfighter's Satellite (feat. Luca The Legacy)",
    # Extras derived from sampled tracks
    "The Starfighter's Satellite", "The Starfighter's Satellite (Hard)",
}

# Cover Up album → all "cover"
# (Danny performing other artists' songs)
COVER_ORIGINALS = {
    "Had A DAT (A Cappella)": "Sublime",
    "Bad Decisions": "Sublime",
    "Industrial Revolution (A Cappella)": "Sublime",
    "Redemption Song (Acoustic-Piano)": "Bob Marley",
    "Doin' Time": "Sublime",
    "Couldn't Get High (A Cappella)": "Sublime",
    "April 29th, 1992 (A Cappella)": "Sublime",
    "Romeo": "Sublime",
    "Garden Grove (A Cappella)": "Sublime",
    "Santeria (A Cappella)": "Sublime",
    "Marley Medley (A Cappella)": "Bob Marley",
    "Rivers of Babylon (Acoustic)": "The Melodians",
    "Wish You Were Here (feat. Blucifer)": "Sublime",
    "Creep (Acoustic)": "Radiohead",
    "Get Out (Acoustic)": "Sublime",
    "Foolish Fool (A Cappella)": "Desmond Dekker",
    "ABCs (feat. Miss Took)": "unknown",
    "This Train": "traditional",
}

# Feels album → "collab" (produced by iLLPeTiLL)
COLLAB_TRACKS = {
    "Freaks", "Freaks (vocals)",
    "Flyin'", "Flyin' (vocals)",
    "Floating (vocals)",
    "For Real (Proof)", "For Real (Proof) (vocals)", "For Real",
    "Fresh", "Fresh (vocals)",
}


def parse_frontmatter(text):
    """Parse YAML frontmatter. Returns (fields_dict, raw_yaml, body)."""
    if not text.startswith("---"):
        return {}, "", text

    end = text.find("---", 3)
    if end == -1:
        return {}, "", text

    yaml_block = text[3:end].strip()
    body = text[end + 3:]

    fields = {}
    for line in yaml_block.split("\n"):
        m = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip().strip('"').strip("'")
            fields[key] = val

    return fields, yaml_block, body


def classify_track(filepath):
    """Determine release type for a track."""
    title = filepath.stem
    text = filepath.read_text()
    fields, _, _ = parse_frontmatter(text)
    album = fields.get("album", "")
    artist_project = fields.get("artist", "")

    # AA Audible → scripture
    if "AA Audible" in str(filepath) or "AA Audible" in artist_project:
        track_type = fields.get("type", "")
        if track_type in ("scripture", "prayer", "devotional", "reflection", "spoken word"):
            return "scripture"
        return "scripture"

    # Cover Up album → cover
    if album == "Cover Up":
        return "cover"

    # Known sampled tracks → sample
    if title in SAMPLED_TRACKS:
        return "mixtape"

    # Check if samples array has a named sample
    if "samples:" in text:
        # Look for 'name:' in the samples section
        lines = text.split("\n")
        in_samples = False
        for line in lines:
            if line.strip().startswith("samples:"):
                in_samples = True
            elif in_samples and re.match(r'\s+- name:', line):
                return "mixtape"
            elif in_samples and re.match(r'^[a-z]', line):
                break

    # Feels / iLLPeTiLL → collab
    if title in COLLAB_TRACKS or fields.get("producer") == "iLLPeTiLL":
        return "collab"

    # Instrumental album — likely original beats by Danny
    if album == "Instrumental":
        return "original"

    # WIP/unreleased
    if fields.get("status") == "wip":
        return "unknown"

    # Everything else needs manual classification
    return "unknown"


def add_release_type(filepath, release_type, dry_run=True):
    """Add or update release_type in frontmatter."""
    text = filepath.read_text()
    fields, yaml_block, body = parse_frontmatter(text)

    if not yaml_block:
        return None

    # Check if release_type already exists
    existing = fields.get("release_type")
    if existing == release_type:
        return None

    if existing:
        # Update existing
        new_yaml = re.sub(
            r'release_type:\s*"?[\w]+"?',
            f'release_type: "{release_type}"',
            yaml_block
        )
    else:
        # Add after album line (or after type line for AA Audible)
        lines = yaml_block.split("\n")
        insert_after = -1
        for i, line in enumerate(lines):
            if line.startswith("album:") or line.startswith("type:"):
                insert_after = i
        if insert_after >= 0:
            lines.insert(insert_after + 1, f'release_type: "{release_type}"')
        else:
            lines.append(f'release_type: "{release_type}"')
        new_yaml = "\n".join(lines)

    new_text = f"---\n{new_yaml}\n---{body}"

    if new_text == text:
        return None

    if not dry_run:
        filepath.write_text(new_text)

    return release_type


def main():
    dry_run = "--dry-run" in sys.argv

    md_files = sorted(
        list(BASE.glob("89 Vision/**/*.md")) +
        list(BASE.glob("AA Audible/**/*.md"))
    )

    print(f"Found {len(md_files)} .md files")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLYING'}\n")

    counts = {}
    changed = 0

    for f in md_files:
        rtype = classify_track(f)
        counts[rtype] = counts.get(rtype, 0) + 1

        result = add_release_type(f, rtype, dry_run)
        if result:
            changed += 1
            rel = f.relative_to(BASE)
            print(f"  {rtype:12s}  {rel}")

    print(f"\n{'Would update' if dry_run else 'Updated'}: {changed} files")
    print(f"\nClassification summary:")
    for rtype, count in sorted(counts.items()):
        print(f"  {rtype:12s}: {count} tracks")

    unknown_count = counts.get("unknown", 0)
    if unknown_count:
        print(f"\n⚠ {unknown_count} tracks classified as 'unknown' — need manual review")

    if dry_run and changed:
        print(f"\nRun without --dry-run to apply.")


if __name__ == "__main__":
    main()
