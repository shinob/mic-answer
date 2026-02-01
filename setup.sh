#!/bin/bash
set -e

cd "$(dirname "$0")"

sudo apt-get install -y libportaudio2

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete. Run with:"
echo "  source .venv/bin/activate"
echo "  python main.py"
