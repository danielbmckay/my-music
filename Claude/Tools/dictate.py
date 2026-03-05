#!/usr/bin/env python3
"""
Dictation — speak into your mic, get text.

Usage:
    dictate              # record 10 seconds, transcribe
    dictate 30           # record 30 seconds
    dictate 60 out.txt   # record 60 seconds, save to out.txt
"""
import sys
import os
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

duration = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
output_file = sys.argv[2] if len(sys.argv) > 2 else "lyrics.txt"
device_id = 1  # Studio Display Microphone

tmp_wav = os.path.join(tempfile.gettempdir(), "dictate_buffer.wav")

print(f"Loading model...")
model = WhisperModel("small", device="cpu", compute_type="int8")

dev = sd.query_devices(device_id)
print(f"Mic: {dev['name']}")
print(f"Recording {duration} seconds — SPEAK NOW\n")

audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype="float32", device=device_id)
sd.wait()

print("Processing...")

# Normalize
peak = np.abs(audio).max()
if peak > 0:
    audio = audio / peak * 0.9

sf.write(tmp_wav, audio, 16000)
segments, _ = model.transcribe(tmp_wav, beam_size=5, language="en")
texts = []
for s in segments:
    t = s.text.strip()
    if t:
        texts.append(t)

if texts:
    result = " ".join(texts)
    print(f"\n  >> {result}\n")
    with open(output_file, "a") as f:
        f.write(result + "\n")
    print(f"Saved to {output_file}")
else:
    print("No speech detected.")

# Keep recordings in Recordings/Desktop/
rec_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Recordings", "Desktop")
os.makedirs(rec_dir, exist_ok=True)
from datetime import datetime
stamp = datetime.now().strftime("%Y-%m-%d %H%M%S")
saved_path = os.path.join(rec_dir, f"Dictation {stamp}.wav")
import shutil
shutil.move(tmp_wav, saved_path)
print(f"Recording: {saved_path}")
