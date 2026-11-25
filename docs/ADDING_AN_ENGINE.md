# Adding an engine

Engines are plain Python files in `server/engines/`. The UI builds itself from
the server, so adding an engine needs no HTML or JavaScript edits.

## 1. Copy the template

```sh
cp server/engines/example.py server/engines/my_engine.py
```

## 2. Implement the contract

A class in that file needs these four things:

| Member | What it returns or does |
| --- | --- |
| `id`, `name`, `tagline`, `note`, `kind` | Plain strings used for the engine rail. `kind` is the badge, e.g. `CPU` or `GPU`. |
| `supports_speed` | `True` if the slider should be enabled. |
| `available()` | `False` when models or dependencies are missing, so the engine is hidden instead of breaking the app. |
| `voices()` | A list of `{"id": "...", "label": "..."}` objects. |
| `synthesize(text, voice, speed, out_path)` | Write a PCM WAV to `out_path`. Nothing else. |

Paths live in `config.json`. Your adapter gets the whole config in
`__init__(self, settings)`; `settings["root"]` is the repo root. A relative
path from your engine settings should be resolved against that root:

```python
from pathlib import Path

def _path(self, key, default=""):
    p = Path(self.cfg.get(key, default))
    return p if p.is_absolute() else Path(self.settings["root"]) / p
```

## 3. Enable it

Add a block to `config.json`; leave `config.example.json` with placeholders:

```json
"engines": {
  "my_engine": {"enabled": true, "model_dir": "./models/my-engine"}
}
```

## 4. Restart

Restart the server or the desktop app. `GET /api/engines` now lists the new
engine with its voices and the UI shows it as a channel in the rail.

## Tips

- Keep heavy imports inside `available()` or `synthesize()` so startup stays fast.
- Return a friendly `RuntimeError` from `synthesize()` on failure; the UI shows it in the status line.
- Write a valid WAV. The server checks for the `RIFF` and `WAVE` headers before replying.
- See `server/engines/phonon.py` for a CLI adapter and `server/engines/chatterbox.py` for an HTTP one.
