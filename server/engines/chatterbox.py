"""Chatterbox adapter for an external Vulkan/HTTP server (GPU)."""
import json
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

_LOCK = threading.Lock()


class ChatterboxEngine:
    id = "chatterbox"
    name = "Chatterbox"
    tagline = "GPU, cloning and emotion tags"
    note = "Try tags like [laugh] or [whispering]. Starts its own server on first use."
    kind = "GPU"
    supports_speed = False
    VOICES = ["Abigail", "Adrian", "Alexander", "Alice", "Austin", "Axel",
              "Connor", "Cora", "Elena", "Eli", "Emily", "Everett", "Gabriel",
              "Gianna", "Henry", "Ian", "Jade", "Jeremiah", "Jordan", "Julian",
              "Layla", "Leonardo", "Michael", "Miles", "Olivia", "Ryan",
              "Taylor", "Thomas"]

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.get("engines", {}).get("chatterbox", {})
        self.api = self.cfg.get("api", "http://127.0.0.1:8087").rstrip("/")

    def _exe(self):
        p = Path(self.cfg.get("exe", ""))
        return p if p.is_absolute() else Path(self.settings["root"]) / p

    def available(self):
        return self._exe().is_file()

    def _up(self):
        try:
            urllib.request.urlopen(self.api + "/v1/audio/voices", timeout=2).close()
            return True
        except Exception:
            return False

    def _ensure(self):
        if self._up():
            return True
        with _LOCK:
            if self._up():
                return True
            exe = self._exe()
            subprocess.Popen([str(exe)], cwd=str(exe.parent),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(40):
                time.sleep(1.5)
                if self._up():
                    return True
        return False

    def voices(self):
        return [{"id": name, "label": name} for name in self.VOICES]

    def synthesize(self, text, voice, speed, out_path):
        if not self._ensure():
            raise RuntimeError("Chatterbox server did not start at " + self.api)
        body = json.dumps({
            "model": self.cfg.get("model", "chatterbox"), "input": text,
            "voice": voice or "Abigail", "response_format": "wav",
        }).encode("utf-8")
        request = urllib.request.Request(
            self.api + "/v1/audio/speech", data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            Path(out_path).write_bytes(response.read())
