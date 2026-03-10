import sys
import os
import torch
from tortoise.utils.audio import load_audio
import torchaudio
import yaml
from tortoise.api import TextToSpeech

def synthesize():
    # Usage: python main.py <text|text_file> [config_file]
    if len(sys.argv) < 2:
        print("Usage: python main.py <text|text_file> [config_file]")
        sys.exit(1)

    text_arg = sys.argv[1]

    default_config_name = sys.argv[2] if len(sys.argv) > 2 else "Default"

    def config_filename(name):
        return name if name.endswith('.yaml') else f"{name}.yaml"

    def resolve_line(line):
        clean_line = line.strip()
        cfg_name = default_config_name
        if clean_line.startswith('[') and ']' in clean_line:
            prefix, remainder = clean_line.split(']', 1)
            maybe_name = prefix.strip('[').strip()
            if maybe_name:
                cfg_name = maybe_name
            clean_line = remainder.strip()
        return cfg_name, clean_line

    if os.path.isfile(text_arg):
        with open(text_arg, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    else:
        raw_text = text_arg

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if not lines:
        print("No text lines found to synthesize.")
        sys.exit(1)

    loaded_voice_samples = {}
    all_audio = []

    for line in lines:
        config_name, text = resolve_line(line)
        if not text:
            continue

        config_file = config_filename(config_name)
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        reference_folder = config.get('reference_folder', 'voices/Default')
        randomness = config.get('randomness', 0.5)
        sample_cache = config.get('sample_cache', 'voice_samples_cache.pt')
        diffusion_temperature = config.get('diffusion_temperature', 1.0)
        preset = config.get('preset', 'fast')

        cache_file = os.path.join(reference_folder, sample_cache)

        if cache_file not in loaded_voice_samples:
            if os.path.exists(cache_file):
                print(f"Loading cached voice samples from {cache_file}")
                voice_samples = torch.load(cache_file)
            else:
                wav_files = [os.path.join(reference_folder, f) for f in os.listdir(reference_folder) if f.endswith('.wav')]
                if not wav_files:
                    print(f"No reference wav files found for config: {config_name}")
                    sys.exit(1)
                voice_samples = [load_audio(wav_file, 22050) for wav_file in wav_files]
                torch.save(voice_samples, cache_file)
                print(f"Processed voice samples cached to {cache_file}")

            loaded_voice_samples[cache_file] = voice_samples

        voice_samples = loaded_voice_samples[cache_file]
        audio = synthesize_batch(text, voice_samples, preset, randomness, diffusion_temperature)
        all_audio.append(audio)

    if all_audio:
        mono_audio = [a.squeeze() for a in all_audio]
        audio_cat = torch.cat(mono_audio, dim=-1).unsqueeze(0)
        
        # Create queue folder if it doesn't exist
        queue_folder = 'queue'
        os.makedirs(queue_folder, exist_ok=True)
        
        # Find next sequence number
        existing_files = [f for f in os.listdir(queue_folder) if f.startswith('generation_') and f.endswith('.pt')]
        if existing_files:
            numbers = []
            for f in existing_files:
                try:
                    num = int(f.replace('generation_', '').replace('.pt', ''))
                    numbers.append(num)
                except ValueError:
                    continue
            next_num = max(numbers) + 1 if numbers else 1
        else:
            next_num = 1
        
        # Save to queue folder with sequential naming
        binary_output = os.path.join(queue_folder, f"generation_{next_num}.pt")
        torch.save({
            'audio': audio_cat.cpu(),
            'sample_rate': 24000
        }, binary_output)
        print(f"Synthesized speech saved to binary format: {binary_output}")
        output_file = f"output_{next_num}.wav"
        print(f"Run 'python scripts/convert.py {binary_output} {output_file}' to convert to wav")
    else:
        print("No audio was generated.")

    # Parallel synthesis function

def synthesize_batch(text, voice_samples, preset, randomness, diffusion_temperature):
    print(f"Synthesizing: {text[:60]}{'...' if len(text) > 60 else ''}")
    audio = TextToSpeech().tts_with_preset(
        text,
        voice_samples=voice_samples,
        preset=preset,
        temperature=randomness,
        diffusion_temperature=diffusion_temperature,
    )
    return audio


if __name__ == "__main__":
    synthesize()