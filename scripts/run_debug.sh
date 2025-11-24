#!/bin/bash

echo "🔍 DEBUG: Starting Graph Editor with debug output..."
echo "🔍 DEBUG: Using python3 instead of python"
echo "🔍 DEBUG: Current directory: $(pwd)"

# Clear Python cache to ensure fresh import
echo "🔍 DEBUG: Clearing Python cache..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "🔍 DEBUG: Running application..."
python3 -u main.py

echo "🔍 DEBUG: Application finished"



