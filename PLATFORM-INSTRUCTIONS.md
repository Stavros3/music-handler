# How To Open The App

## Windows

Double-click:

`Run Duplicate Music Finder - Windows.bat`

## macOS

Double-click:

`Run Duplicate Music Finder - macOS.command`

If macOS says Apple could not verify the file:

1. Right-click the file
2. Choose `Open`
3. Click `Open` again

If it is still blocked:

1. Open `System Settings`
2. Go to `Privacy & Security`
3. Click `Open Anyway`

If macOS says you do not have the appropriate access privileges, run:

```bash
chmod +x "Run Duplicate Music Finder - macOS.command"
```

If needed, also run:

```bash
xattr -d com.apple.quarantine "Run Duplicate Music Finder - macOS.command"
```

After the launcher starts once, it will try to clear the macOS quarantine flag automatically.

## Linux

Make the file executable once:

```bash
chmod +x "Run Duplicate Music Finder - Linux.sh"
```

Then open:

`Run Duplicate Music Finder - Linux.sh`

## What The App Does

1. Choose a folder
2. Scan for duplicate `.mp3` and `.wav` files
3. Listen if needed
4. Choose which file to keep
5. Send the rest to Trash / Recycle Bin
