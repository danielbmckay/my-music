#!/usr/bin/env python3
"""
Batch transcribe tracks using faster-whisper.
Prioritizes vocal-only and voice memo sources.
Outputs raw transcriptions to Claude/transcriptions/ for review.
"""
import os
import sys
import json
from faster_whisper import WhisperModel

BASE = "/Users/danielbmckay/Desktop/My Music"
OUT_DIR = os.path.join(BASE, "Claude", "transcriptions")
os.makedirs(OUT_DIR, exist_ok=True)

# Track name -> best audio source path (relative to BASE)
# Tier 1: Isolated vocals
# Tier 2: Voice memos (Final/Raw Cuts)
# Tier 3: Full mixes (last resort)
TRACKS = [
    # Tier 1 — isolated vocals
    ("Floating (vocals)", "89 Vision/Albums/Feels/Floating (vocals).aif"),
    ("Fresh (vocals)", "89 Vision/Albums/Feels/Fresh (vocals).aif"),
    ("Sum Freestyle (vocals)", "89 Vision/Extras/Sum Freestyle (vocals).aif"),
    ("Above The Clouds (raw vocals)", "89 Vision/Extras/Above The Clouds (raw vocals).aif"),

    # Tier 2 — voice memos
    ("Blurring The Lines (Acoustic)", "Recordings/iPhone/Final Cuts/Blurring The Lines.m4a"),
    ("Quality Music (Acoustic)", "Recordings/iPhone/Raw Cuts/Quality Muzak (Acoustic).m4a"),
    ("Sandy Eggo", "Recordings/iPhone/Raw Cuts/Sandy Eggo Freestyle [Bang Bang-Still D.R.E., Dr. Dre].m4a"),
    ("Satellite", "Recordings/iPhone/Raw Cuts/Satellite Freestyle [Bang Bang, Dr. Dre].m4a"),
    ("They Lied To Me", "Recordings/iPhone/Final Cuts/They Lied To Me [Green Day, Longview].m4a"),
    ("Dollar Tree", "Recordings/iPhone/Final Cuts/Dollar Tree Freestyle Part 1.m4a"),
    ("Dollar Tree Pt2", "Recordings/iPhone/Final Cuts/Dollar Tree Freestyle Part 2.m4a"),
    ("Dollar Tree Pt3", "Recordings/iPhone/Final Cuts/Dollar Tree Freestyle Part 3.m4a"),
    ("Jazzy", "Recordings/iPhone/Raw Cuts/Jazzy Freestyle.m4a"),
    ("Jr. Gong", "Recordings/iPhone/Raw Cuts/Jr. Gong's Freestyle [Life's Been Good, Dirty Heads].m4a"),
    ("Slave Quarter", "Recordings/iPhone/Final Cuts/Slave Quarter Freestyle.m4a"),
    ("The Words", "Recordings/iPhone/Raw Cuts/The Words Freestyle.m4a"),

    # Tier 3 — full mixes (may struggle but worth trying)
    ("89 Vision (Reggae)", "89 Vision/Albums/89 Vision/'89 Vision (Reggae).aif"),
    ("Above The Clouds", "89 Vision/Albums/Free Style/Above The Clouds.aif"),
    ("Bee Kind (Remixed)", "89 Vision/Albums/Free Style/Bee Kind (Remixed).aif"),
    ("Chimes", "89 Vision/Albums/Free Style/Chimes.aif"),
    ("FTW", "89 Vision/Albums/Free Style/FTW.aif"),
    ("Jain", "89 Vision/Albums/Free Style/Jain.aif"),
    ("Rainy Daze", "89 Vision/Albums/Free Style/Rainy Daze.aif"),
    ("Fresh", "89 Vision/Albums/Feels/Fresh.aif"),
    ("Where Do We Go?", "89 Vision/Albums/Sunny Daze/Where Do We Go?.aif"),
    ("Bee Kind (Electric)", "89 Vision/Extras/Bee Kind (Electric).aif"),
    ("Mary Jane", "89 Vision/Extras/Mary Jane.aif"),
    ("Me And My Arrow", "89 Vision/Extras/Me And My Arrow.aif"),
    ("Reggae Love", "89 Vision/Extras/Reggae Love.aif"),
    ("The Bug", "89 Vision/Extras/The Bug.aif"),
    ("The Call", "89 Vision/Extras/The Call.aif"),
    ("The King", "89 Vision/Extras/The King.aif"),
    ("The Starfighter's Satellite", "89 Vision/Extras/The Starfighter's Satellite.aif"),
    ("The Starfighter's Satellite (Hard)", "89 Vision/Extras/The Starfighter's Satellite (Hard).aif"),
    ("This Train", "89 Vision/Extras/This Train.aif"),
    ("This Train (remixed)", "89 Vision/Extras/This Train (remixed).aif"),
]

def transcribe_track(model, name, audio_rel):
    audio_path = os.path.join(BASE, audio_rel)
    if not os.path.exists(audio_path):
        return name, None, f"FILE NOT FOUND: {audio_path}"

    try:
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            language="en",
        )
        lines = []
        for s in segments:
            text = s.text.strip()
            if text:
                lines.append(f"[{s.start:.1f}s - {s.end:.1f}s] {text}")

        if not lines:
            return name, [], "No speech detected"

        return name, lines, None
    except Exception as e:
        return name, None, str(e)

def main():
    model_size = sys.argv[1] if len(sys.argv) > 1 else "small"
    print(f"Loading {model_size} model...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print(f"Model loaded. Transcribing {len(TRACKS)} tracks...\n")

    results = {}
    for i, (name, audio_rel) in enumerate(TRACKS):
        print(f"[{i+1}/{len(TRACKS)}] {name}...", end=" ", flush=True)
        name, lines, error = transcribe_track(model, name, audio_rel)

        if error:
            print(f"ERROR: {error}")
            results[name] = {"error": error}
        elif lines:
            print(f"OK ({len(lines)} segments)")
            results[name] = {"segments": lines}
            # Write individual file
            safe_name = name.replace("/", "-").replace("?", "").replace("'", "")
            out_path = os.path.join(OUT_DIR, f"{safe_name}.txt")
            with open(out_path, "w") as f:
                f.write(f"# {name}\n\n")
                for line in lines:
                    f.write(line + "\n")
        else:
            print("No speech detected")
            results[name] = {"error": "No speech detected"}

    # Summary
    ok = sum(1 for v in results.values() if "segments" in v)
    fail = len(results) - ok
    print(f"\nDone: {ok} transcribed, {fail} failed/empty")

    # Write summary
    with open(os.path.join(OUT_DIR, "_summary.json"), "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
