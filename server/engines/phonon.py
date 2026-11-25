"""Phonon adapter (standalone ptts CLI, CPU)."""
import json
import subprocess
from pathlib import Path


class PhononEngine:
    id = "phonon"
    name = "Phonon"
    tagline = "Fastest, about 3x realtime"
    note = "Handles numbers, prices and dates well. Best for quick replies."
    kind = "CPU"
    supports_speed = False

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.get("engines", {}).get("phonon", {})

    def _path(self, key, default=""):
        p = Path(self.cfg.get(key, default))
        return p if p.is_absolute() else Path(self.settings["root"]) / p

    def available(self):
        return self._path("exe").is_file() and self._path("model_dir").is_dir()

    def voices(self):
        items = [{"id": "default", "label": "Default, built in"}]
        path = self._path("voices_file")
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                items.append({
                    "id": str(self._path("voice_dir") / entry["filename"]).replace("\\", "/"),
                    "label": "%s (%s, %s)" % (entry.get("name", "voice"),
                                             entry.get("locale", "en"),
                                             entry.get("gender", "voice")),
                })
        return items

    def synthesize(self, text, voice, speed, out_path):
        args = [
            str(self._path("exe")), "--model", str(self._path("model_dir")),
            "--lang", self.cfg.get("lang", "en"), "--quant", self.cfg.get("quant", "q8"),
            "--voice", voice or "default", text, "-o", out_path,
        ]
        result = subprocess.run(args, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Phonon failed").strip()[-800:])
