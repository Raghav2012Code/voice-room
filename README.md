# Voice Room

A local, self-hosted text-to-speech studio. Type text, pick an engine and voice,
and hear the result generated on your own machine. Nothing is uploaded.

The UI is a dark broadcast console: engine channel strip, voice picker, speed,
chunked long-text playback, live status, generation stats and a WAV download.
The host and UI are engine-agnostic. Engines are small adapters in
`server/engines/`, so adding any local TTS means adding one file and one config
block. See [docs/ADDING_AN_ENGINE.md](docs/ADDING_AN_ENGINE.md).

## Run it

```sh
python -m server.server
```

Open `http://127.0.0.1:8766/`. The shipped `config.example.json` enables a
sine-wave example engine so you can try the whole flow with no models installed.

To use your own engines:

```sh
cp config.example.json config.json
```

Edit `config.json`: set `models_dir`, enable the adapters you have, and point
each one at its files. `config.json` is gitignored and stays on your machine.

Optional adapter dependencies:

```sh
pip install -r requirements-adapters.txt
```

## Native Windows app

The `desktop/` folder is a Tauri v2 shell. It starts the configured backend,
waits for the port, opens a native window and stops the backend when you close
the window.

```sh
cd desktop
npm install
npx tauri build
```

Put a `config.json` next to the built executable (or set `VOICE_ROOM_CONFIG`)
with absolute paths to your Python interpreter and this repo's
`server/server.py`:

```json
{
  "server": {"command": ["C:/path/to/venv/Scripts/python.exe", "-m", "server.server"],
             "cwd": "C:/path/to/voice-room", "port": 8766,
             "log": "C:/path/to/voice-room/server.log"}
}
```

The window URL is `http://127.0.0.1:<port>/`, so changing the port also needs a
corresponding change in `desktop/src-tauri/tauri.conf.json` if you use the
bundled window, or just keep 8766.

## API

- `GET /api/health` - status, model root and loaded engine ids
- `GET /api/engines` - engines, voices and capabilities (`/api/voices` is an alias)
- `POST /api/speak` - JSON `{"engine","text","voice","speed"}` returns raw WAV with `X-Gen-Seconds`, `X-Audio-Seconds` and `X-Sample-Rate` headers

## Tests

```sh
python -m unittest discover -s tests -v
```

The tests use the example adapter, so no TTS models or extra packages needed.

## Included adapters

| Adapter | Needs | Notes |
| --- | --- | --- |
| example | nothing | Sine wave, useful for verification |
| phonon | standalone `ptts` CLI + model | Fast CPU engine, many voices |
| kokoro | `kokoro-onnx`, numpy, soundfile + ONNX files | 54 voices, several languages |
| kitten | `kittenml`, soundfile + model folder | Small English voice set |
| chatterbox | external HTTP/Vulkan server | Voice tags and cloning, GPU |

## Privacy

The server binds to `127.0.0.1` by default. Text and audio stay on your
machine. No telemetry, no accounts, no API keys.

## License

MIT. See [LICENSE](LICENSE).
