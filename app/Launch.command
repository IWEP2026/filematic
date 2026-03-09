#!/bin/bash
cd "$(dirname "$0")"
echo "Checking dependencies..."
pip3 install Pillow --break-system-packages --quiet 2>/dev/null
echo "Launching Filematic..."
python3 "main.py"
