---
title: Configuration
sidebar_label: Configuration
sidebar_position: 3
description: The config.json keys for the server and each engine.
---

# Configuration

The server reads `config.json` from the repository root. If that file does not exist, it falls back to `config.example.json`.

`config.json` is gitignored. Keep machine specific paths there and leave the example file with placeholders.

## Top level

```json
{
  "server": { "host": "127.0.0.1", "port": 8766 },
  "models_dir": "./models",
  "engines": {
    "example": { "enabled": true }
  }
}
```

| Key | Default | Meaning |
| --- | --- | --- |
| `server.host` | `127.0.0.1` | Bind address. Keep it on localhost unless you add authentication and a rate limit. |
| `server.port` | `8766` | HTTP port. |
| `models_dir` | `./models` | Informational root shown by `/api/health`. Adapters can use it or their own paths. |
| `engines` | `{}` | Per adapter settings. An engine only loads when `enabled` is `true`. |

## Engine blocks

Each adapter is free to define its own keys. These are the ones included in the repo:

| Adapter | Keys |
| --- | --- |
| `phonon` | `exe`, `model_dir`, `voices_file`, `voice_dir`, `lang`, `quant` |
| `kokoro` | `onnx`, `voices` |
| `kitten` | `model_dir`, `voices`, `sample_rate` |
| `chatterbox` | `exe`, `api`, `model` |

A full example:

```json
{
  "server": { "host": "127.0.0.1", "port": 8766 },
  "models_dir": "G:/tts-models",
  "engines": {
    "example": { "enabled": false },
    "phonon": {
      "enabled": true,
      "exe": "G:/tts-models/phonon/ptts.exe",
      "model_dir": "G:/tts-models/phonon",
      "voices_file": "G:/tts-models/phonon-voices/voices.jsonl",
      "voice_dir": "G:/tts-models/phonon-voices/voices"
    },
    "kokoro": {
      "enabled": true,
      "onnx": "G:/tts-models/kokoro/kokoro-v1.0.onnx",
      "voices": "G:/tts-models/kokoro/voices-v1.0.bin"
    }
  }
}
```

Relative paths resolve against the repository root in the included adapters. Absolute paths work too.

## Desktop configuration

The Tauri shell uses a separate `config.json` next to its executable, or the file named by `VOICE_ROOM_CONFIG`. Its shape is about starting the backend:

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

See [Desktop app](/docs/desktop-app) for the build and launch steps.

## Changing the port

The browser UI follows `server.port`. The bundled desktop window loads `http://127.0.0.1:8766/` by default, so if you change the port also change the window URL in `desktop/tauri.conf.json`, or keep 8766.
