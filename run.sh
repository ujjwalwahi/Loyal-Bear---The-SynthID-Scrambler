#!/usr/bin/env bash
set -e

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+ first."
    exit 1
fi

python3 main.py
