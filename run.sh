#!/usr/bin/env bash
set -e

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+ first."
    exit 1
fi

if [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing torch (CPU)..."
    .venv/bin/pip install --quiet torch torchvision
    echo "Installing dependencies..."
    .venv/bin/pip install --quiet -r requirements.txt
fi

.venv/bin/python main.py
