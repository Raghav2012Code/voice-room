"""Kokoro adapter (82M ONNX, CPU). Optional deps: kokoro-onnx, numpy, soundfile."""
import importlib.util
import threading
from pathlib import Path

_LOCK = threading.Lock()
_MODEL = None


class KokoroEngine:
    id = "kokoro"
    name = "Kokoro"
    tagline = "54 voices, richest delivery"
    note = "af_/am_ US English, bf_/bm_ UK, hf_/hm_ Hindi. Slower, best on long text."
    kind = "CPU"
    supports_speed = True
    LANG = {
        "af": "en-us", "am": "en-us", "bf": "en-gb", "bm": "en-gb",
        "ef": "es", "em": "es", "ff": "fr", "fm": "fr", "hf": "hi", "hm": "hi",
        "if": "it", "im": "it", "jf": "ja", "jm": "ja", "pf": "pt-br", "pm": "pt-br",
        "zf": "zh", "zm": "zh",
    }

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.get("engines", {}).get("kokoro", {})
        global _MODEL
        _MODEL = None

    def _path(self, key, default=""):
        p = Path(self.cfg.get(key, default))
        return p if p.is_absolute() else Path(self.settings["root"]) / p

    def available(self):
        deps = all(importlib.util.find_spec(m) for m in ("kokoro_onnx", "numpy", "soundfile"))
        return deps and self._path("onnx").is_file() and self._path("voices").is_file()

    def voices(self):
        import numpy as np
        with np.load(str(self._path("voices"))) as data:
            return [{"id": name, "label": name} for name in sorted(data.files)]

    def synthesize(self, text, voice, speed, out_path):
        global _MODEL
        import soundfile as sf
        with _LOCK:
            if _MODEL is None:
                from kokoro_onnx import Kokoro
                _MODEL = Kokoro(str(self._path("onnx")), str(self._path("voices")))
            chosen = voice or "af_heart"
            language = self.LANG.get(chosen[:2], "en-us")
            audio, rate = _MODEL.create(text, voice=chosen, speed=float(speed), lang=language)
            sf.write(out_path, audio, rate)
