---
title: Add an engine
sidebar_label: Adding an engine
sidebar_position: 2
description: Implement the adapter contract and make a local TTS engine appear in Voice Room.
---

# Add an engine

Engines are plain Python. There is no plugin package, no entry point and no frontend edit. Copy the example, implement three methods, enable the engine in config, restart the server.

## 1. Copy the template

```bash
cp server/engines/example.py server/engines/my_engine.py
```

## 2. Implement the contract

A class in the file needs these members:

| Member | What it does |
| --- | --- |
| `id`, `name`, `tagline`, `note`, `kind` | Strings used by the UI. `kind` is the badge, for example `CPU` or `GPU`. |
| `supports_speed` | `True` if the Speed slider should apply. |
| `available()` | Return `False` when models or dependencies are missing. The engine is then hidden instead of breaking startup. |
| `voices()` | Return a list of `{"id": "...", "label": "..."}` objects. |
| `synthesize(text, voice, speed, out_path)` | Write a PCM WAV to `out_path`. That is the whole job. |

`__init__(self, settings)` receives the parsed config, with `settings["root"]` set to the repository root.

## 3. A minimal adapter

```python
import wave

class MyEngine:
    id = "my_engine"
    name = "My engine"
    tagline = "What makes it different"
    note = "A sentence shown in the sidebar."
    kind = "CPU"
    supports_speed = False

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.get("engines", {}).get("my_engine", {})

    def available(self):
        return True

    def voices(self):
        return [{"id": "default", "label": "Default"}]

    def synthesize(self, text, voice, speed, out_path):
        # Replace this with your model call.
        with wave.open(out_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(b"\x00\x00" * 24000)
```

## 4. Resolve paths safely

Put paths in config, not in code. A relative path should resolve against the repo root:

```python
from pathlib import Path

def _path(self, key, default=""):
    path = Path(self.cfg.get(key, default))
    return path if path.is_absolute() else Path(self.settings["root"]) / path
```

Then `available()` can check that the file or folder exists before claiming to work.

## 5. Enable it

Add a block to `config.json`:

```json
{
  "engines": {
    "my_engine": {
      "enabled": true,
      "model_dir": "./models/my-engine"
    }
  }
}
```

Restart the server. `GET /api/engines` should now include `my_engine`, and the rail should show it on the next page load.

## 6. Handle failures clearly

Raise a `RuntimeError` with a short, useful message. The UI puts it in the status line. Do not let a failed synthesis return an empty file.

```python
if not model_loaded:
    raise RuntimeError("Model files not found. Check my_engine.model_dir in config.json.")
```

## Tips

- Keep heavy imports inside `available()` or `synthesize()` so startup stays fast.
- Write a real WAV. The server checks the `RIFF` and `WAVE` headers before replying.
- The server calls `synthesize` on a worker thread. Use a lock around a model object that is not thread safe.
- See `server/engines/phonon.py` for a command line adapter and `server/engines/chatterbox.py` for an HTTP adapter.
