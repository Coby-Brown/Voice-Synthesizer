import sys
import os
from pydub import AudioSegment

if len(sys.argv) < 3:
    print("Usage: python train.py <mp3_folder> <reference_folder>")
    sys.exit(1)

mp3_folder = sys.argv[1]
reference_folder = sys.argv[2]

os.makedirs(reference_folder, exist_ok=True)

for file in os.listdir(mp3_folder):
    if file.endswith('.mp3'):
        audio = AudioSegment.from_mp3(os.path.join(mp3_folder, file))
        wav_file = os.path.join(reference_folder, file.replace('.mp3', '.wav'))
        audio.export(wav_file, format='wav')
        print(f"Converted {file} to {wav_file}")

print("Training complete, reference audios prepared.")