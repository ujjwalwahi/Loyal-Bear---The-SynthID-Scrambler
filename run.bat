@echo off
title Loyal Bear - The SynthID Scrambler

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing torch - CPU...
    .venv\Scripts\python.exe -m pip install --quiet torch torchvision
    echo Installing dependencies...
    .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
)

.venv\Scripts\python.exe main.py
if %errorlevel% neq 0 pause
