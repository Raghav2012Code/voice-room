"""Kitten TTS 2 Mini adapter (CPU). Optional dep: kittenml, soundfile."""
import importlib.util
import threading
from pathlib import Path

_LOCK = threading.Lock()
_MODEL = None


class KittenEngine:
    id = "kitten"
    name = "Kitten 2 Mini"
    tagline = "New, many voices"
    note = "English voice pack. First run loads its voice files."
    kind = "CPU"
    supports_speed = True

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.get("engines", {}).get("kitten", {})
        global _MODEL
        _MODEL = None

    def _path(self, key, default=""):
        p = Path(self.cfg.get(key, default))
        return p if p.is_absolute() else Path(self.settings["root"]) / p

    def available(self):
        deps = all(importlib.util.find_spec(m) for m in ("kittenml", "soundfile"))
        return deps and self._path("model_dir").is_dir()

    def voices(self):
        names = self.cfg.get("voices") or [
            "Eleanor", "Martha", "Serena", "Iris", "Grace", "Edith", "Diana",
            "Otis", "Vincent", "Max", "Danny",
        ]
        return [{"id": name, "label": name} for name in names]

    def synthesize(self, text, voice, speed, out_path):
        global _MODEL
        import soundfile as sf
        with _LOCK:
            if _MODEL is None:
                from kittenml import KittenTTS
                _MODEL = KittenTTS(str(self._path("model_dir")))
            audio = _MODEL.generate(text, voice=voice or self.voices()[0]["id"],
                                    speed=float(speed))
            sf.write(out_path, audio, int(self.cfg.get("sample_rate", 24000)))
