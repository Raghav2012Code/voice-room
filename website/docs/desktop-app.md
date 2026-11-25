---
title: Desktop app
sidebar_label: Desktop app
sidebar_position: 4
description: Build and run the native Windows window for Voice Room.
---

# Desktop app

The `desktop/` folder is a Tauri v2 shell. It starts the configured Python backend, waits for the port, opens one native window, and stops the backend when the window closes.

## What you need

- Windows 10 or 11, x64.
- Rust and the GNU or MSVC toolchain.
- Node and npm.
- WebView2, which is part of Windows 11 and present on most Windows 10 systems.
- Python 3.10 or newer for the backend.

## Build

From the repository root:

```bash
cd desktop
npm install
npx tauri build
```

The app is written to `desktop/target/release/voice-room.exe`. The NSIS installer is written to `desktop/target/release/bundle/nsis/`.

The v0.1.0 release already includes a signed out installer. Building locally is useful if you change the shell.

## Point it at your backend

Put a `config.json` next to the executable, or set `VOICE_ROOM_CONFIG` to its path:

```json
{
  "server": {
    "command": ["C:/path/to/venv/Scripts/python.exe", "-m", "server.server"],
    "cwd": "C:/path/to/voice-room",
    "port": 8766,
    "log": "C:/path/to/voice-room/server.log"
  }
}
```

`command` is the full argument list. `cwd` is where the server should run, normally the repo root so relative model paths work. If the port is already open, the app attaches to the existing server instead of starting a second one.

## How closing works

The app stores the child process it spawned. On `WindowEvent::Destroyed` it kills and waits for that process, so closing the window does not leave a Python server behind.

## Ports

The window loads `http://127.0.0.1:<port>/` from config. If you change the port, also update the window URL in `desktop/tauri.conf.json`, or keep 8766.
