---
title: Quickstart
sidebar_label: Quickstart
sidebar_position: 2
description: Run Voice Room locally and generate your first clip.
---

# Quickstart

This gets you from a fresh clone to hearing a clip with no model downloads. The shipped example engine writes a sine wave, which proves the UI, server and API all work.

## Before you start

- Python 3.10 or newer.
- A terminal.

Clone the repository and enter it:

```bash
git clone https://github.com/Raghav2012Code/voice-room.git
cd voice-room
```

Node and Rust are only needed for the optional desktop app.

## 1. Start the server

```bash
python -m server.server
```

You should see:

```text
Voice Room running at http://127.0.0.1:8766/
```

:::note
Keep this terminal open while you use the app. Closing it stops the server.
:::

## 2. Open the console

Open [http://127.0.0.1:8766/](http://127.0.0.1:8766/) in your browser.

The engine rail lists **Example tone**. Leave the voice on 440 Hz.

## 3. Generate a clip

1. Type a sentence in the Script box.
2. Press **Speak**, or use **Ctrl+Enter**.
3. The Monitor shows a player, the time taken, audio length and throughput.
4. **Download wav** saves the take.

If that works, the host is healthy. You can now point it at a real engine.

## 4. Enable a real engine

Copy the example config and edit it:

```bash
cp config.example.json config.json
```

In `config.json`, set `models_dir` and enable an adapter, for example:

```json
{
  "models_dir": "./models",
  "engines": {
    "phonon": {
      "enabled": true,
      "exe": "./models/phonon/ptts.exe",
      "model_dir": "./models/phonon"
    }
  }
}
```

Restart the server, reload the page, and the engine appears in the rail.

Some adapters need extra Python packages:

```bash
pip install -r requirements-adapters.txt
```

## 5. Try long text

Paste a long article and press Speak. The script is split into sentence sized parts, so the first audio arrives quickly while later parts render. **Stop** cancels between parts and keeps what has already played.

## Next

- [Configuration](/docs/configuration) for every key.
- [Add an engine](/docs/engines/adding-an-engine) for a model that is not included.
- [Troubleshooting](/docs/troubleshooting) if an engine is missing or a clip fails.
