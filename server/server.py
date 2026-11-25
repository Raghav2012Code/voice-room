"""Voice Room HTTP host: static UI plus a tiny JSON/WAV API.

Run from the repo root: python -m server.server
All configuration lives in config.json (see config.example.json).
"""
import argparse
import json
import os
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .registry import load as load_engines

ROOT = Path(__file__).resolve().parent.parent
STATIC = {
    "/": ("ui/index.html", "text/html; charset=utf-8"),
    "/index.html": ("ui/index.html", "text/html; charset=utf-8"),
    "/styles.css": ("ui/styles.css", "text/css; charset=utf-8"),
    "/app.js": ("ui/app.js", "application/javascript; charset=utf-8"),
    "/favicon.svg": ("ui/favicon.svg", "image/svg+xml"),
}


def load_config(path=None):
    config_path = Path(path) if path else (ROOT / "config.json")
    if not config_path.exists():
        config_path = ROOT / "config.example.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.setdefault("server", {})
    config.setdefault("models_dir", "./models")
    config.setdefault("engines", {})
    config["root"] = str(ROOT)
    config["config_path"] = str(config_path.resolve())
    return config


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    context = None

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _wav(self, data, headers):
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data)))
        for key, value in headers.items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        ctx = self.context
        try:
            if path in STATIC:
                rel, mime = STATIC[path]
                data = (ROOT / rel).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            elif path == "/api/health":
                self._json({"ok": True, "models": ctx["config"]["models_dir"],
                            "engines": list(ctx["engines"])})
            elif path in ("/api/engines", "/api/voices"):
                self._json({"engines": ctx["payload"]})
            else:
                self._json({"error": "Not found"}, 404)
        except Exception as exc:
            self._json({"error": str(exc)[:600]}, 500)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/speak":
            self._json({"error": "Not found"}, 404)
            return
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(size) or b"{}")
            engine_id = req.get("engine") or ""
            text = (req.get("text") or "").strip()
            voice = req.get("voice") or None
            speed = float(req.get("speed", 1.0))
            if not text:
                raise ValueError("Type something to speak first.")
            engine = self.context["engines"].get(engine_id)
            if engine is None:
                raise ValueError("Unknown engine: " + str(engine_id))
            started = time.perf_counter()
            engine.synthesize(text, voice, speed, tmp)
            elapsed = time.perf_counter() - started
            data = Path(tmp).read_bytes()
            if not data.startswith(b"RIFF") or not data[8:12] == b"WAVE":
                raise RuntimeError("The engine did not write a WAV file.")
            self._wav(data, {
                "X-Gen-Seconds": "%.2f" % elapsed,
                "X-Audio-Seconds": "%.2f" % wav_duration(data),
                "X-Sample-Rate": str(sample_rate(data)),
            })
        except Exception as exc:
            self._json({"error": str(exc)[:600]}, 500)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/"):
            print("%s %s" % (self.command, self.path), flush=True)


def wav_duration(data):
    import io
    import wave
    try:
        with wave.open(io.BytesIO(data), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def sample_rate(data):
    import struct
    try:
        return struct.unpack_from("<I", data, 24)[0]
    except Exception:
        return 0


def build(config_path=None, port_override=None):
    config = load_config(config_path)
    engines, skipped = load_engines(
        config, ROOT / "server" / "engines", config["engines"]
    )
    payload = []
    for engine in engines.values():
        try:
            voices = engine.voices() or []
        except Exception as exc:
            print("voices() failed for %s: %s" % (engine.id, exc), flush=True)
            voices = []
        payload.append({
            "id": engine.id,
            "name": getattr(engine, "name", engine.id),
            "tagline": getattr(engine, "tagline", ""),
            "note": getattr(engine, "note", ""),
            "kind": getattr(engine, "kind", "CPU"),
            "speed": getattr(engine, "supports_speed", False),
            "voices": voices,
        })
    for name, reason in skipped:
        print("skip %s: %s" % (name, reason), flush=True)

    class BoundHandler(Handler):
        pass
    BoundHandler.context = {"config": config, "engines": engines, "payload": payload}
    host = config["server"].get("host", "127.0.0.1")
    port = port_override if port_override is not None else int(config["server"].get("port", 8766))
    return ThreadingHTTPServer((host, port), BoundHandler)


def main():
    parser = argparse.ArgumentParser(description="Voice Room local TTS host")
    parser.add_argument("--config", help="path to config.json")
    parser.add_argument("--port", type=int, help="override the configured port")
    args = parser.parse_args()
    httpd = build(args.config, args.port)
    httpd.daemon_threads = True
    print("Voice Room running at http://%s:%d/" % httpd.server_address, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
