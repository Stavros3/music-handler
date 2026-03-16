#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

xattr -dr com.apple.quarantine "$SCRIPT_DIR" >/dev/null 2>&1 || true

if command -v python3 >/dev/null 2>&1; then
  PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_EXE="python"
else
  osascript -e 'display dialog "Python 3 was not found. Please install Python 3 and try again." buttons {"OK"} default button "OK"'
  exit 1
fi

"$PYTHON_EXE" -m pip install -r app/requirements.txt pyinstaller
"$PYTHON_EXE" -m PyInstaller --noconfirm build.spec

osascript -e 'display dialog "macOS standalone build created in the dist folder." buttons {"OK"} default button "OK"'
