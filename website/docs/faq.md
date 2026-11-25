---
title: FAQ
sidebar_label: FAQ
sidebar_position: 7
description: Short answers to the questions people ask first.
---

# FAQ

## Is it really offline?

Yes. The server binds to `127.0.0.1`, the UI is served from the same process, and there is no telemetry. Models are local files. If you never install a model, the example engine still works offline.

## Are models included?

No. The repository is the host and the interface. Model weights are large and licensed separately, so each adapter points at files you provide. `requirements-adapters.txt` lists the optional Python packages.

## Can I use my own TTS model?

Yes, if you can call it from Python and write a WAV. Copy `server/engines/example.py`, implement `voices()` and `synthesize()`, enable it in `config.json`, and restart. See [Add an engine](/docs/engines/adding-an-engine).

## Does it work on macOS or Linux?

The browser UI and the Python server are cross platform. The native shell in `desktop/` is built and released for Windows x64. On other systems, run `python -m server.server` and open the local URL.

## Can it speak Tamil or Indian English?

That depends on the engine, not the host. The included Kokoro adapter has Hindi voices alongside English and several European languages. Tamil or Indian English needs an adapter whose model supports those voices. The host will show any engine you add.

## Can my friends use it over the network?

Not safely as shipped. It is a localhost tool with no authentication. Adding remote access needs a private network or an identity gate, plus a rate limit and a text cap. Do not port forward it as is.

## Why is there no character limit?

Long text is split in the browser and synthesized in parts. The server has no cap because it assumes a trusted local user. A public deployment would need one.

## What license is it under?

MIT. The adapters call third party models and tools that have their own licenses. Check each model before redistributing it.

## How do I update it?

```bash
git pull
pip install -r requirements-adapters.txt
```

Rebuild the desktop app only if the shell changed:

```bash
cd desktop
npm install
npx tauri build
```
