#!/bin/bash
set -e

# Check for Python 3.10
if ! python3.10 --version &>/dev/null; then
  echo "Python 3.10 is required. Please install it first."
  exit 1
fi

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env if .env does not exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env file created from .env.example. Please update it with your API keys."
fi

echo "Setup complete. Activate your venv with 'source venv/bin/activate' and run 'python main.py' to start." 