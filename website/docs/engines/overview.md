---
title: Engines
sidebar_label: Overview
sidebar_position: 1
description: How Voice Room discovers engines and what adapters are included.
---

# Engines

An engine is a Python file in `server/engines/` with a class that can list voices and write a WAV file. The registry imports every file in that folder at startup and keeps the engines that are enabled in `config.json` and report themselves as available.

The UI never contains a list of engine names. It calls `GET /api/engines` and builds the rail from the response, so a new adapter shows up without a frontend change.

## Included adapters

| Adapter | Runtime needs | Notes |
| --- | --- | --- |
| `example` | none | Sine wave. Useful for verifying the host. |
| `phonon` | standalone `ptts` CLI and a model folder | Fast CPU engine with a local voice catalog. |
| `kokoro` | `kokoro-onnx`, numpy, soundfile, ONNX model and voices file | 54 voices across several languages. |
| `kitten` | `kittenml`, soundfile, model folder | Small English voice set. |
| `chatterbox` | an external HTTP or Vulkan server | Voice tags and cloning. GPU recommended. |

No model files are bundled with the repository. Each adapter reads its paths from `config.json`.

## The lifecycle

1. The server starts and reads `config.json`.
2. The registry loads each `.py` file in `server/engines/`.
3. Disabled engines are skipped.
4. Enabled engines are asked `available()`. If models or dependencies are missing, they are skipped and the reason is printed.
5. The UI calls `/api/engines` and shows the survivors.

Skipped engines do not break the app. Check the server terminal for lines beginning with `skip` when an engine you expected is missing.

## Voices and capabilities

Each engine returns metadata in the `/api/engines` response:

| Field | Meaning |
| --- | --- |
| `id` | Stable identifier used by `POST /api/speak`. |
| `name` | Label in the engine rail. |
| `tagline` | One line under the name. |
| `note` | Longer note shown in the sidebar. |
| `kind` | Badge text, usually `CPU` or `GPU`. |
| `speed` | Whether the Speed slider applies. |
| `voices` | List of `{ id, label }` objects. |

## Next

- [Add an engine](/docs/engines/adding-an-engine): the contract and a full walkthrough.
- [Configuration](/docs/configuration): the engine settings block.
