#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_EXE=""

if command -v python3 >/dev/null 2>&1; then
  PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_EXE="python"
fi

if [ -z "$PYTHON_EXE" ]; then
  osascript -e 'display dialog "Python 3 was not found. Please install Python 3 and try again." buttons {"OK"} default button "OK"'
  exit 1
fi

if ! "$PYTHON_EXE" -c "import PySide6, send2trash" >/dev/null 2>&1; then
  "$PYTHON_EXE" -m pip install -r app/requirements.txt
fi

"$PYTHON_EXE" app/app.py
