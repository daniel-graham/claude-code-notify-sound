#!/usr/bin/env python3
"""Generate sounds/claude-ember.wav: a soft, low tongue-drum knock that rings
out on its own harmonics, with a warm damped reverb. Pure stdlib.

Usage: python3 scripts/generate_ember.py [output.wav]
"""
import math
import os
import struct
import sys
import wave

SR = 44100
FREQ = 146.83 * 1.25  # ~F#3
DUR = 1.6


def env(t, attack, decay):
    a = min(1.0, t / attack) if attack > 0 else 1.0
    return a * math.exp(-t / decay)


def struck(t, f, body=0.55, bend=0.12, knock_decay=0.04,
           partials=((1, 1.0, 1.0), (2, 0.25, 0.5), (3, 0.08, 0.35))):
    # Pitched knock that settles into its own ringing body
    k = env(t, 0.001, knock_decay) * math.sin(2 * math.pi * f * (1 + bend * math.exp(-t / 0.01)) * t)
    r = sum(g * env(t, 0.004, body * ds) * math.sin(2 * math.pi * f * n * t) for n, g, ds in partials)
    return 0.8 * k + 0.5 * r


def soft_reverb(buf, mix=0.18, damp=0.45):
    # Combs with a one-pole lowpass in the feedback path: warm, non-metallic tail
    out = [0.0] * len(buf)
    for d_ms, g in ((31.3, 0.70), (36.7, 0.68), (40.9, 0.66), (45.1, 0.64)):
        d = int(d_ms * SR / 1000)
        c = [0.0] * len(buf)
        lp = 0.0
        for i, x in enumerate(buf):
            fb = c[i - d] if i >= d else 0.0
            lp = (1 - damp) * fb + damp * lp
            c[i] = x + g * lp
            out[i] += c[i] * 0.25
    return [(1 - mix) * a + mix * b for a, b in zip(buf, out)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "sounds", "claude-ember.wav")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = int(DUR * SR)
    buf = [struck(i / SR, FREQ) if i < int(1.5 * SR) else 0.0 for i in range(n)]
    buf = soft_reverb(buf)
    fade = int(0.08 * SR)
    for i in range(fade):
        buf[-1 - i] *= i / fade
    peak = max(abs(x) for x in buf) or 1.0
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.5 * 32767)) for x in buf))
    print(path)


if __name__ == "__main__":
    main()
