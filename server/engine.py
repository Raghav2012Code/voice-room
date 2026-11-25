"""The contract a Voice Room adapter implements.

Adapters do not have to subclass this class; the registry discovers them by
duck typing. Subclassing is just a convenient way to inherit the defaults.
"""

class Engine:
    id = "example"
    name = "Example"
    tagline = ""
    note = ""
    kind = "CPU"          # shown as a badge in the UI, e.g. CPU or GPU
    supports_speed = False

    def __init__(self, settings):
        """settings is the whole config.json, with 'root' added."""
        self.settings = settings

    def available(self):
        """Return False to hide this engine when its models/deps are absent."""
        return True

    def voices(self):
        """Return a list of {"id": str, "label": str}."""
        return []

    def synthesize(self, text, voice, speed, out_path):
        """Write a PCM WAV to out_path. Voice and speed come from the UI."""
        raise NotImplementedError

    def close(self):
        """Optional cleanup when the server exits."""
