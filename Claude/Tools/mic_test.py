#!/usr/bin/env python3
"""Quick mic test — shows volume levels so you can verify your mic works."""
import sys
import numpy as np
import sounddevice as sd

device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

dev = sd.query_devices(device_id)
print(f"Testing: {dev['name']}")
print("Speak into your mic. You should see the bar move.")
print("Ctrl+C to stop.\n")

def callback(indata, frames, time, status):
    volume = np.abs(indata).mean()
    bars = int(volume * 500)
    meter = "#" * min(bars, 60)
    print(f"\r  vol: {volume:.5f} |{meter:<60}|", end="", flush=True)

try:
    with sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                       blocksize=8000, device=device_id, callback=callback):
        while True:
            sd.sleep(100)
except KeyboardInterrupt:
    print("\n\nDone.")
