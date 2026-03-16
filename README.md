# Duplicate Music Finder

## Download And Open

1. Download this project from GitHub as a ZIP
2. Extract the ZIP
3. Open the extracted folder
4. Double-click the launcher for your system:

- Windows: `Run Duplicate Music Finder - Windows.bat`
- macOS: `Run Duplicate Music Finder - macOS.command`
- Linux: `Run Duplicate Music Finder - Linux.sh`

For packaged downloads and OS-specific steps for opening unsigned app builds, see `downloads/README.md`.

Python must already be installed on the computer.

If Python or the required packages are missing, the launcher will try to install them.

## Install Python First

If Python is not installed:

- Windows or macOS: download it from [python.org/downloads](https://www.python.org/downloads/)
- Linux: install Python 3 from your system package manager

Windows note:

- during installation, enable `Add Python to PATH`

After Python is installed, open this folder and double-click the launcher for your system.

## macOS Note

If macOS says Apple could not verify the file:

1. Right-click `Run Duplicate Music Finder - macOS.command`
2. Choose `Open`
3. Click `Open` again

If it is still blocked:

1. Open `System Settings`
2. Go to `Privacy & Security`
3. Click `Open Anyway`

If macOS says you do not have the appropriate access privileges, open Terminal in this folder and run:

```bash
chmod +x "Run Duplicate Music Finder - macOS.command"
```

If needed, also run:

```bash
xattr -d com.apple.quarantine "Run Duplicate Music Finder - macOS.command"
```

After the launcher starts once, it will try to clear the macOS quarantine flag automatically.

## Credits

By `@stavik.music`

## What It Does

1. Choose a folder
2. Scan for duplicate `.mp3` and `.wav` files
3. Listen if needed
4. Choose which file to keep
5. Send the rest to Trash / Recycle Bin

## Standalone Build

To build a standalone app:

- Windows: `build-windows.bat`
- macOS: `build-macos.command`
- Linux: `build-linux.sh`

The packaged app will be created in the `dist` folder.

Note:

- Windows standalone can be built on Windows
- macOS standalone should be built on macOS and will create a `.app` bundle
- Linux standalone should be built on Linux
