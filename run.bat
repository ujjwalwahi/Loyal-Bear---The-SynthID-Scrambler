@echo off
title Loyal Bear - The SynthID Scrambler

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

python main.py
if %errorlevel% neq 0 pause
