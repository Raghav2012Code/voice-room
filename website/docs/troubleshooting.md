---
title: Troubleshooting
sidebar_label: Troubleshooting
sidebar_position: 6
description: Fix the common reasons an engine or a clip does not work.
---

# Troubleshooting

Start with the server terminal. It prints skipped engines and request lines. Then check `GET /api/health` and `GET /api/engines`.

## The page will not load

- Confirm the server is running: `python -m server.server`.
- Open `http://127.0.0.1:8766/`, not a `file://` path.
- If the port is busy, stop the old process or start with `--port 8767`.

```bash
python -m server.server --port 8767
```

## An engine is missing from the rail

The registry skips engines that are disabled or unavailable.

1. Check that the engine has `"enabled": true` in `config.json`.
2. Check every path in that engine's block. A typo means `available()` returns `False`.
3. Install its optional packages from `requirements-adapters.txt`.
4. Read the server terminal for a line beginning with `skip` and the reason.

## Speak returns a model or dependency error

The adapter reached `synthesize()` but could not finish. The status line shows the message. Common causes:

- The model folder exists but a file inside it is missing.
- An optional package was installed into a different Python environment than the one running the server.
- The engine needs a sidecar server that did not start, such as Chatterbox on port 8087.

## The audio is silent or very short

Try the example engine first. If it works, the host and UI are fine and the problem is inside the adapter or its model. Check that the adapter writes a PCM WAV and not raw samples.

## The desktop app opens but the page is blank

- Confirm a `config.json` exists beside the executable or `VOICE_ROOM_CONFIG` points at one.
- Confirm `cwd` points at the repo root.
- Check the `log` path for the backend output.
- Make sure the configured port matches the window URL in `desktop/tauri.conf.json`.

## A long script stops partway

Press Stop only if you want to cancel. Otherwise leave it running; each part is synthesized in order. A slow engine on a long script takes time. The Monitor updates as parts arrive.

## Tests fail

```bash
python -m unittest discover -s tests -v
```

The tests use the example engine and need no models. If they fail on a clean clone, check the Python version, 3.10 or newer, and that you are in the repository root.
