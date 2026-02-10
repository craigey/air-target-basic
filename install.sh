#!/usr/bin/env bash
set -e

echo "🔧 Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-rpi.gpio \
    python3-venv \
    python3-opencv \
    python3-rpi.gpio \
    libatlas-base-dev \
    v4l-utils


echo "🐍 Creating virtual environment..."
python3 -m venv venv --system-site-packages

echo "📦 Activating venv & installing Python deps..."
source venv/bin/activate
pip install --upgrade pip
pip install flask numpy scipy
pip3 -install python3-opencv

mkdir certs
mkdir shots
cd certs
openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes   -keyout raspberrypi.key -out raspberrypi.crt   -subj "/CN=raspberrypi"   -addext "subjectAltName=DNS:raspberrypi,DNS:raspberrypi.local,IP:192.168.0.84"
cd ..

echo "✅ Setup complete"

echo "➡ Run with: source venv/bin/activate && python app.py"
