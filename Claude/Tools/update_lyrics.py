#!/usr/bin/env python3
"""
Read Whisper transcriptions and update corresponding .md files,
replacing 'Lyrics not yet transcribed' with the transcribed text.
Strips timestamps, joins into clean lyrics.
"""
import os
import re

BASE = "/Users/danielbmckay/Desktop/My Music"
TRANS_DIR = os.path.join(BASE, "Claude", "transcriptions")

# Map: transcription filename (without .txt) -> .md file path (relative to BASE)
MAPPING = {
    "Floating (vocals)": "89 Vision/Albums/Feels/Floating (vocals).md",
    "Fresh (vocals)": "89 Vision/Albums/Feels/Fresh (vocals).md",
    "Fresh": "89 Vision/Albums/Feels/Fresh.md",
    "Sum Freestyle (vocals)": "89 Vision/Extras/Sum Freestyle (vocals).md",
    "Above The Clouds (raw vocals)": "89 Vision/Extras/Above The Clouds (raw vocals).md",
    "Blurring The Lines (Acoustic)": "89 Vision/Albums/89 Vision/Blurring The Lines (Acoustic).md",
    "Quality Music (Acoustic)": "89 Vision/Albums/89 Vision/Quality Music (Acoustic).md",
    "Sandy Eggo": "89 Vision/Albums/89 Vision/Sandy Eggo.md",
    "Satellite": "89 Vision/Albums/89 Vision/Satellite.md",
    "They Lied To Me": "89 Vision/Albums/89 Vision/They Lied To Me.md",
    "89 Vision (Reggae)": "89 Vision/Albums/89 Vision/'89 Vision (Reggae).md",
    "Dollar Tree": "89 Vision/Albums/Free Style/Dollar Tree.md",
    "Jazzy": "89 Vision/Albums/Free Style/Jazzy.md",
    "Jr. Gong": "89 Vision/Albums/Free Style/Jr. Gong.md",
    "Slave Quarter": "89 Vision/Albums/Free Style/Slave Quarter.md",
    "The Words": "89 Vision/Albums/Free Style/The Words.md",
    "Above The Clouds": "89 Vision/Albums/Free Style/Above The Clouds.md",
    "Bee Kind (Remixed)": "89 Vision/Albums/Free Style/Bee Kind (Remixed).md",
    "Chimes": "89 Vision/Albums/Free Style/Chimes.md",
    "FTW": "89 Vision/Albums/Free Style/FTW.md",
    "Jain": "89 Vision/Albums/Free Style/Jain.md",
    "Rainy Daze": "89 Vision/Albums/Free Style/Rainy Daze.md",
    "Where Do We Go": "89 Vision/Albums/Sunny Daze/Where Do We Go?.md",
    "Mary Jane": "89 Vision/Extras/Mary Jane.md",
    "Me And My Arrow": "89 Vision/Extras/Me And My Arrow.md",
    "Reggae Love": "89 Vision/Extras/Reggae Love.md",
    "The Bug": "89 Vision/Extras/The Bug.md",
    "The Call": "89 Vision/Extras/The Call.md",
    "The King": "89 Vision/Extras/The King.md",
    "The Starfighters Satellite": "89 Vision/Extras/The Starfighter\u2019s Satellite.md",
    "The Starfighters Satellite (Hard)": "89 Vision/Extras/The Starfighter\u2019s Satellite (Hard).md",
    "This Train": "89 Vision/Extras/This Train.md",
    "This Train (remixed)": "89 Vision/Extras/This Train (remixed).md",
    "Bee Kind (Electric)": "89 Vision/Extras/Bee Kind (Electric).md",
}

def extract_lyrics(trans_path):
    """Read transcription file, strip timestamps, return clean lyrics."""
    with open(trans_path, "r") as f:
        lines = f.readlines()

    lyrics_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip timestamp prefix like [0.0s - 2.8s]
        match = re.match(r'\[\d+\.\d+s\s*-\s*\d+\.\d+s\]\s*(.*)', line)
        if match:
            lyrics_lines.append(match.group(1))
        else:
            lyrics_lines.append(line)

    return "\n".join(lyrics_lines)


def update_md(md_path, lyrics):
    """Replace 'Lyrics not yet transcribed' in .md file with actual lyrics."""
    with open(md_path, "r") as f:
        content = f.read()

    if "Lyrics not yet transcribed" not in content:
        return False

    # Add whisper draft note
    replacement = f"*[Whisper draft — needs review]*\n\n{lyrics}"
    content = content.replace("Lyrics not yet transcribed", replacement)

    with open(md_path, "w") as f:
        f.write(content)
    return True


def main():
    updated = 0
    skipped = 0
    errors = 0

    for trans_name, md_rel in MAPPING.items():
        trans_path = os.path.join(TRANS_DIR, f"{trans_name}.txt")
        md_path = os.path.join(BASE, md_rel)

        if not os.path.exists(trans_path):
            print(f"  SKIP (no transcription): {trans_name}")
            skipped += 1
            continue

        if not os.path.exists(md_path):
            # Try without smart quote
            alt = md_path.replace("\u2019", "'")
            if os.path.exists(alt):
                md_path = alt
            else:
                print(f"  ERROR (md not found): {md_rel}")
                errors += 1
                continue

        lyrics = extract_lyrics(trans_path)
        if not lyrics.strip():
            print(f"  SKIP (empty transcription): {trans_name}")
            skipped += 1
            continue

        if update_md(md_path, lyrics):
            print(f"  OK: {trans_name} -> {md_rel}")
            updated += 1
        else:
            print(f"  SKIP (no placeholder): {trans_name}")
            skipped += 1

    # Handle Dollar Tree parts 2 & 3 — append to Dollar Tree.md
    dt_md = os.path.join(BASE, "89 Vision/Albums/Free Style/Dollar Tree.md")
    for part in ["Dollar Tree Pt2", "Dollar Tree Pt3"]:
        trans_path = os.path.join(TRANS_DIR, f"{part}.txt")
        if os.path.exists(trans_path):
            lyrics = extract_lyrics(trans_path)
            if lyrics.strip():
                with open(dt_md, "a") as f:
                    label = part.replace("Dollar Tree ", "")
                    f.write(f"\n\n### {label}\n\n{lyrics}")
                print(f"  APPENDED: {part} -> Dollar Tree.md")

    print(f"\nDone: {updated} updated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
