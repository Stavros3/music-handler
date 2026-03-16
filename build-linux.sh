#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_EXE="python"
else
  echo "Python 3 was not found."
  exit 1
fi

"$PYTHON_EXE" -m pip install -r app/requirements.txt pyinstaller
"$PYTHON_EXE" -m PyInstaller --noconfirm build.spec

echo "Linux standalone build created in the dist folder."
