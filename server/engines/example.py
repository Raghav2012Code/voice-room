"""Minimal adapter, works with zero dependencies. Copy this to add an engine."""
import math
import struct
import wave


class ExampleEngine:
    id = "example"
    name = "Example tone"
    tagline = "Test adapter, no models needed"
    note = "A plain sine wave so you can verify the UI and API before adding real engines."
    kind = "CPU"
    supports_speed = True

    def __init__(self, settings):
        self.settings = settings

    def available(self):
        return True

    def voices(self):
        return [
            {"id": "440", "label": "440 Hz"},
            {"id": "660", "label": "660 Hz"},
        ]

    def synthesize(self, text, voice, speed, out_path):
        rate = 24000
        frequency = int(voice or "440")
        seconds = min(2.0, max(0.25, len(text) / 90.0 * float(speed or 1.0)))
        with wave.open(out_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            frames = bytearray()
            for i in range(int(rate * seconds)):
                value = int(9000 * math.sin(2 * math.pi * frequency * i / rate))
                frames.extend(struct.pack("<h", value))
            w.writeframes(frames)
