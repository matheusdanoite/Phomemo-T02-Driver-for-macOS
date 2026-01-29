#!/bin/bash
# Wrapper script for macOS PDF Services
# This script is called by the macOS Print Dialog when "Print to Phomemo" is selected.

# Path to your project
PROJECT_DIR="/Users/matheusdanoite/Desktop/phomemo"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
SCRIPT="$PROJECT_DIR/pdf_to_phomemo.py"

# Logging for debugging
LOGfile="/tmp/phomemo_print.log"
echo "$(date): Iniciando impressão via PDF Service" >> "$LOGfile"
echo "Args: $@" >> "$LOGfile"

cd "$PROJECT_DIR"

# "$@" contains the file paths passed by macOS
"$VENV_PYTHON" "$SCRIPT" "$@" >> "$LOGfile" 2>&1

echo "$(date): Fim" >> "$LOGfile"
