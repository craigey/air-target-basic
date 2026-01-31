#!/usr/bin/env bash
set -e

echo "🔧 Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    libatlas-base-dev

echo "🐍 Creating virtual environment..."
python3 -m venv venv

echo "📦 Activating venv & installing Python deps..."
source venv/bin/activate
pip install --upgrade pip
pip install flask numpy scipy

echo "✅ Setup complete"
echo "➡ Run with: source venv/bin/activate && python app.py"