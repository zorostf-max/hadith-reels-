#!/usr/bin/env python3
"""Check which vowel a narrator used inside a word (e.g. the first vowel of «عُبادة»).

Usage: python3 tool/check_vowel.py <clip.mp3> <start_s> <end_s>
Get the word's start/end from ElevenLabs creative_transcribe_audio (`words`, costs 0 credits).
Prints mean F1/F2 over the voiced frames of the first ~40% of the word and a guess:
  /u/ (damma): F2 low  (< ~1100 Hz)      /i/ (kasra): F2 high (> ~1800 Hz)
  /a/ (fatha): F1 high (> ~600 Hz), F2 in between.
Rough acoustic check, not proof: when unsure, say so in the Telegram preview.
Needs: pip install praat-parselmouth --break-system-packages
"""
import sys
import parselmouth

clip, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
snd = parselmouth.Sound(clip)
fm = snd.to_formant_burg(max_number_of_formants=5, maximum_formant=5000)
pitch = snd.to_pitch()
end = t0 + (t1 - t0) * 0.4
f1s, f2s = [], []
t = t0
while t <= end:
    v = pitch.get_value_at_time(t)
    f1, f2 = fm.get_value_at_time(1, t), fm.get_value_at_time(2, t)
    if v == v and v and f1 == f1 and f2 == f2 and 200 < f1 < 1100:
        f1s.append(f1); f2s.append(f2)
    t += 0.01
if not f1s:
    sys.exit("no voiced frames in that window; widen it")
F1, F2 = sum(f1s) / len(f1s), sum(f2s) / len(f2s)
guess = "u (damma)" if F2 < 1100 else "i (kasra)" if F2 > 1800 else ("a (fatha)" if F1 > 600 else "unclear")
print(f"frames={len(f1s)} F1={F1:.0f} F2={F2:.0f} -> {guess}")
