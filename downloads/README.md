# Downloads

This folder contains packaged builds of Duplicate Music Finder.

## Files In This Folder

- `Duplicate Music Finder Windows.exe`: standalone Windows build
- `MacOS - Duplicate Music Finder.zip`: macOS packaged build

If a Linux build is added later, include it in this folder and follow the Linux steps below.

## Windows

### Open The App

1. Double-click `Duplicate Music Finder Windows.exe`.

### If Windows Blocks The App

Because the app is not code-signed, Windows may show a Microsoft Defender SmartScreen warning.

1. Click `More info`
2. Click `Run anyway`

If Windows still blocks the file:

1. Right-click `Duplicate Music Finder Windows.exe`
2. Choose `Properties`
3. On the `General` tab, check `Unblock` if it appears
4. Click `Apply`
5. Open the app again

## macOS

### Open The App

1. Unzip `MacOS - Duplicate Music Finder.zip`
2. Open `Duplicate Music Finder.app`

### If macOS Blocks The App

Because the app is not signed or notarized, macOS may block it with a security warning.

1. Right-click the app
2. Choose `Open`
3. Click `Open` again

If macOS still blocks it:

1. Open `System Settings`
2. Go to `Privacy & Security`
3. Scroll to the security message for the app
4. Click `Open Anyway`
5. Confirm by clicking `Open`

If the extracted file is quarantined, run one of these commands in Terminal from the extracted folder:

```bash
chmod +x "Duplicate Music Finder.app/Contents/MacOS/Duplicate Music Finder"
```

or, if macOS still refuses to open it:

```bash
xattr -dr com.apple.quarantine "Duplicate Music Finder.app"
```

## Linux

There is no Linux packaged download in this folder right now, but if one is added later these are the expected steps.

### Open The App

If the Linux download is a shell script or extracted binary, make it executable first:

```bash
chmod +x "./Duplicate Music Finder"
```

Then run it:

```bash
./Duplicate Music Finder
```

### If Linux Blocks The App

Linux usually does not require code signing, but the desktop environment may block direct launching until the file is marked executable.

1. Right-click the file
2. Open `Properties`
3. Enable `Allow executing file as program` if that option is available
4. Launch the file again

## What The App Does

1. Choose a folder
2. Scan for duplicate `.mp3` and `.wav` files
3. Listen if needed
4. Choose which file to keep
5. Send the rest to Trash or Recycle Bin