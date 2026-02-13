def synthesize():
    import sys
    import os
    import torch
    from tortoise.api import TextToSpeech
    from tortoise.utils.audio import load_audio
    import torchaudio
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import yaml


    # Usage: python main.py <text|text_file> <output_file> [config_file]
    if len(sys.argv) < 3:
        print("Usage: python main.py <text|text_file> <output_file> [config_file]")
        sys.exit(1)

    text_arg = sys.argv[1]
    output_file = sys.argv[2]
    if text_arg.find("[", 0, 10) != -1:
        config_name = text_arg.split("]", 1)[0].strip("[")
    else:
        config_name = sys.argv[3] if len(sys.argv) > 3 else "Default"
    config_file = config_name if config_name.endswith('.yaml') else f"{config_name}.yaml"

    # Load config
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}


    reference_folder = config.get('reference_folder', 'voices/Default')
    randomness = config.get('randomness', 0.5)
    sample_cache = config.get('sample_cache', 'voice_samples_cache.pt')
    diffusion_temperature = config.get('diffusion_temperature', 1.0)
    preset = config.get('preset', 'fast')

    # Caching processed voice samples
    cache_file = os.path.join(reference_folder, sample_cache)

    if os.path.exists(cache_file):
        print(f"Loading cached voice samples from {cache_file}")
        voice_samples = torch.load(cache_file)
    else:
        wav_files = [os.path.join(reference_folder, f) for f in os.listdir(reference_folder) if f.endswith('.wav')]
        if not wav_files:
            print("No reference wav files found")
            sys.exit(1)
        voice_samples = [load_audio(wav_file, 22050) for wav_file in wav_files]
        torch.save(voice_samples, cache_file)
        print(f"Processed voice samples cached to {cache_file}")

    # Batch helper
    def batch_lines(lines, batch_size):
        for i in range(0, len(lines), batch_size):
            yield lines[i:i+batch_size]

    # Prepare batches of text
    texts = []
    if os.path.isfile(text_arg):
        with open(text_arg, 'r', encoding='utf-8') as f:
            all_lines = [line.strip() for line in f if line.strip()]
        texts = [' '.join(batch) for batch in batch_lines(all_lines, 1)]
    else:
        texts = [text_arg]
    
    all_audio = []
    with ProcessPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(synthesize_batch, text, voice_samples, preset, randomness, diffusion_temperature) for text in texts]
        for future in as_completed(futures):
            audio = future.result()
            all_audio.append(audio)

    if all_audio:
        mono_audio = [a.squeeze() for a in all_audio]
        audio_cat = torch.cat(mono_audio, dim=-1).unsqueeze(0)
        torchaudio.save(output_file, audio_cat.cpu(), 24000)
        print(f"Synthesized speech saved to {output_file}")
    else:
        print("No audio was generated.")

    # Parallel synthesis function

def synthesize_batch(text, voice_samples, preset, randomness, diffusion_temperature):
    from tortoise.api import TextToSpeech
    print(f"Synthesizing: {text[:60]}{'...' if len(text) > 60 else ''}")
    audio = TextToSpeech().tts_with_preset(
        text,
        voice_samples=voice_samples,
        preset=preset,
        temperature=randomness,
        diffusion_temperature=diffusion_temperature,
    )
    return audio

def main():
    synthesize()

if __name__ == "__main__":
    main()