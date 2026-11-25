---
title: API reference
sidebar_label: API reference
sidebar_position: 5
description: The local HTTP endpoints for health, engines and speech.
---

# API reference

The server binds to `127.0.0.1:8766` by default. There is no authentication because it is a localhost tool. Do not expose it to a network without adding authentication, a rate limit and a text cap.

## GET /api/health

Returns a small status object.

```bash
curl http://127.0.0.1:8766/api/health
```

```json
{
  "ok": true,
  "models": "./models",
  "engines": ["example"]
}
```

## GET /api/engines

Returns the engine list and each engine's voices. `/api/voices` is an alias kept for older clients.

```bash
curl http://127.0.0.1:8766/api/engines
```

```json
{
  "engines": [
    {
      "id": "example",
      "name": "Example tone",
      "tagline": "Test adapter, no models needed",
      "note": "A plain sine wave so you can verify the UI and API.",
      "kind": "CPU",
      "speed": true,
      "voices": [
        { "id": "440", "label": "440 Hz" },
        { "id": "660", "label": "660 Hz" }
      ]
    }
  ]
}
```

## POST /api/speak

Synthesizes one piece of text and returns a WAV body.

```bash
curl -X POST http://127.0.0.1:8766/api/speak \
  -H "Content-Type: application/json" \
  -d '{"engine":"example","text":"Hello from Voice Room.","voice":"440","speed":1.0}' \
  --output hello.wav
```

Request body:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `engine` | string | yes | Engine `id` from `/api/engines`. |
| `text` | string | yes | Text to speak. Empty text is rejected. |
| `voice` | string | no | Voice `id`. The engine chooses a default when omitted. |
| `speed` | number | no | Voice rate. Ignored by engines with `supports_speed: false`. |

Response headers:

| Header | Meaning |
| --- | --- |
| `X-Gen-Seconds` | Wall clock seconds spent generating. |
| `X-Audio-Seconds` | Duration of the returned audio. |
| `X-Sample-Rate` | Sample rate in Hz. |

Success returns `200` with `Content-Type: audio/wav`. Errors return a JSON object with an `error` string and a `500` status, for example an unknown engine or a missing model file.

## Calling it from Python

```python
import json
import urllib.request

body = json.dumps({
    "engine": "example",
    "text": "Generated on this machine.",
    "voice": "440",
    "speed": 1.0,
}).encode("utf-8")

request = urllib.request.Request(
    "http://127.0.0.1:8766/api/speak",
    data=body,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=120) as response:
    open("out.wav", "wb").write(response.read())
```
