#!/usr/bin/env python3
"""
Convert binary audio format (.pt) to .wav format
Usage: python convert.py <input.pt> <output.wav>
"""

import sys
import os
import torch
import torchaudio


def convert_to_wav(input_file, output_file):
    """Convert a .pt binary audio file to .wav format"""
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    if not input_file.endswith('.pt'):
        print(f"Warning: Input file should be a .pt file")
    
    # Load the binary audio data
    print(f"Loading audio from {input_file}...")
    data = torch.load(input_file)
    
    # Extract audio tensor and sample rate
    audio = data['audio']
    sample_rate = data['sample_rate']
    
    # Save as wav
    print(f"Converting to wav format...")
    torchaudio.save(output_file, audio, sample_rate)
    print(f"Successfully saved to {output_file}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio.shape}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert.py <input.pt> <output.wav>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    convert_to_wav(input_file, output_file)


if __name__ == "__main__":
    main()
