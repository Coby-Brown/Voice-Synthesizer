#!/bin/bash
# Script to set up Python virtual environment and install all packages found in current venv311

set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv311" ]; then
    python3.11 -m venv venv311
fi

# Activate the virtual environment
source venv311/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all detected packages (from current venv311)
pip install torch==2.1.2 torchaudio==2.1.2 torchcodec==0.9.1 tqdm==4.67.3 transformers==4.31.0 librosa==0.11.0 soundfile==0.13.1 soxr==1.0.0 einops==0.8.2 rotary-embedding-torch==0.8.9 safetensors==0.7.0 numpy==1.26.4 scipy==1.17.0 pyyaml==6.0.3 fastapi==0.129.0 uvicorn==0.40.0 aiohttp==3.13.3 starlette==0.52.1 pydantic==2.12.5 pydantic-core==2.41.5 python-dotenv==1.2.1 tqdm==4.67.3 requests==2.32.5 yarl==1.22.0 typing-extensions==4.15.0 tortoise-tts==3.0.0

# Add any other packages you need below
# pip install <other-package>

echo "Virtual environment set up and dependencies installed."
