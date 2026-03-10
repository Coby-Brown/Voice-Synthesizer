#!/usr/bin/env python3
"""
Convert binary audio format (.pt) to .wav format
Usage: 
  python convert.py <output.wav>              - Auto-convert next queue file
  python convert.py <input.pt> <output.wav>   - Convert specific file
"""

import sys
import os
import torch
import torchaudio


STATE_FILE = '.convert_state'
QUEUE_FOLDER = 'queue'


def get_last_converted():
    """Get the last converted generation number from state file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0


def save_last_converted(gen_number):
    """Save the last converted generation number to state file"""
    with open(STATE_FILE, 'w') as f:
        f.write(str(gen_number))


def get_next_queue_file():
    """Find the next generation file in the queue"""
    if not os.path.exists(QUEUE_FOLDER):
        print(f"Error: Queue folder '{QUEUE_FOLDER}' not found")
        sys.exit(1)
    
    last_converted = get_last_converted()
    next_gen = last_converted + 1
    
    # Find the next available generation file
    while True:
        next_file = os.path.join(QUEUE_FOLDER, f"generation_{next_gen}.pt")
        if os.path.exists(next_file):
            return next_file, next_gen
        elif next_gen > last_converted + 100:  # Safety limit
            print(f"Error: No more generation files found in queue after generation_{last_converted}")
            print(f"Available files in queue:")
            queue_files = sorted([f for f in os.listdir(QUEUE_FOLDER) if f.startswith('generation_') and f.endswith('.pt')])
            for f in queue_files:
                print(f"  {f}")
            sys.exit(1)
        next_gen += 1


def convert_to_wav(input_file, output_file, gen_number=None):
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
    
    # Also save to old_generations folder with sequential numbering
    old_gen_folder = 'old_generations'
    os.makedirs(old_gen_folder, exist_ok=True)
    
    # Find next sequence number
    existing_files = [f for f in os.listdir(old_gen_folder) if f.startswith('synthesis_') and f.endswith('.wav')]
    if existing_files:
        numbers = []
        for f in existing_files:
            try:
                num = int(f.replace('synthesis_', '').replace('.wav', ''))
                numbers.append(num)
            except ValueError:
                continue
        next_num = max(numbers) + 1 if numbers else 1
    else:
        next_num = 1
    
    old_gen_file = os.path.join(old_gen_folder, f"synthesis_{next_num}.wav")
    torchaudio.save(old_gen_file, audio, sample_rate)
    print(f"Also saved to {old_gen_file}")
    
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio.shape}")
    
    # Update state if this was a queue file
    if gen_number is not None:
        save_last_converted(gen_number)
        print(f"State updated: Last converted generation_{gen_number}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python convert.py <output.wav>              - Auto-convert next queue file")
        print("  python convert.py [input.pt] <output.wav>   - Convert specific file")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # Auto-convert next queue file
        output_file = sys.argv[1]
        input_file, gen_number = get_next_queue_file()
        print(f"Auto-converting next queue file: {input_file}")
        convert_to_wav(input_file, output_file, gen_number)
    else:
        # Manual file specification
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        # Check if this is a queue file to update state
        gen_number = None
        if input_file.startswith(QUEUE_FOLDER + '/') and 'generation_' in input_file:
            try:
                gen_number = int(input_file.split('generation_')[1].split('.')[0])
            except (IndexError, ValueError):
                pass
        
        convert_to_wav(input_file, output_file, gen_number)


if __name__ == "__main__":
    main()
