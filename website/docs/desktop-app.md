---
title: Desktop app
sidebar_label: Desktop app
sidebar_position: 4
description: Build and run the native Windows window for Voice Room.
---

# Desktop app

The `desktop/` folder is a Tauri v2 shell. It opens a native window on a bundled splash page, starts the configured Python backend, and navigates the window to the local UI once the backend answers. The backend keeps running when the window is closed to the tray.

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

The project ships a signed out installer. Building locally is useful if you change the shell.

## Point it at your backend

Put a `config.json` next to the executable, or set `VOICE_ROOM_CONFIG` to its path:

```json
{
  "server": {
    "command": ["C:/path/to/venv/Scripts/python.exe", "-m", "server.server"],
    "cwd": "C:/path/to/voice-room",
    "port": 8766,
    "log": "C:/path/to/voice-room/server.log"
  },
  "desktop": { "tray": true }
}
```

`command` is the full argument list. `cwd` is where the server should run, normally the repo root so relative model paths work. If the port is already open, the app attaches to the existing server instead of starting a second one.

`desktop.tray` defaults to `true`. Set it to `false` to run without a tray icon: closing the window then quits the app and stops the backend child, which is the behaviour of earlier versions.

## Startup sequence

The window is built immediately with the bundled page in `desktop/frontend/index.html`, which shows "Starting the local engine" with a pulsing dot. Nothing waits on the port before the window appears.

A background thread starts the backend when the port is free and polls the port for up to 20 seconds. When the port answers, the app navigates the window to `http://127.0.0.1:<port>/` on the UI thread. If the backend does not answer in time, or the command cannot be started, the bundled page switches to an error panel. The panel tells you to open the configured log file if there is one.

## Tray

The tray icon is built from the app window icon and uses the tooltip "Voice Room". Its menu contains:

- `Open Voice Room`: shows, unminimizes and focuses the window.
- `Start with Windows`: a check item for the per-user autostart entry.
- `Quit`: stops the backend child the app spawned, then exits.

A left click on the tray icon shows and focuses the window as well.

## Close to tray

While the tray is enabled, closing the window hides it and the backend keeps running. Quitting happens through the tray `Quit` item. If the app attached to a server that was already running, `Quit` leaves that server alone.

If the window is destroyed anyway, cleanup still kills the backend child as a safety net.

## Start with Windows

`Start with Windows` writes a per-user autostart entry through `reg.exe`, without an extra crate:

- Key: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- Value name: `Voice Room`
- Data: the current executable in quotes followed by ` --minimized`, for example `"C:\Apps\Voice Room\voice-room.exe" --minimized`

The check state is read at startup with `reg query`. Turning the item off deletes the value with `reg delete`.

## Start minimized

When the process arguments contain `--minimized`, the window is built hidden, so an autostart launch lands in the tray only. The backend starts and the window navigates the same way as a normal launch, so the UI is ready when you open it from the tray.

With `desktop.tray` set to `false`, do not use `--minimized`, because there is no tray icon to restore the window from.

## Single instance and window state

Only one copy of the app runs. A second launch shows, unminimizes and focuses the existing `main` window instead of starting another app or server.

The window size and position persist between launches. The first run uses 1240x840 and is centered. Later runs restore the saved size and position.

## Ports

The window URL is built at runtime from `server.port`, so changing the port in `config.json` is enough. There is no window URL in `desktop/tauri.conf.json` to update.
