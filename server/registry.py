"""Discover and instantiate TTS adapters from server/engines/*.py."""
import importlib.util
import sys
from pathlib import Path


def _is_adapter(obj, module_name):
    return (
        isinstance(obj, type)
        and obj.__module__ == module_name
        and hasattr(obj, "id")
        and callable(getattr(obj, "voices", None))
        and callable(getattr(obj, "synthesize", None))
    )


def load(settings, engines_dir, enabled):
    """Return (dict of id -> instance, list of (filename, reason) skipped)."""
    engines, skipped = {}, []
    folder = Path(engines_dir)
    for path in sorted(folder.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = "voice_room_adapter_" + path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            classes = [v for v in vars(module).values() if _is_adapter(v, module_name)]
            if not classes:
                skipped.append((path.name, "no adapter class found"))
                continue
            engine = classes[0](settings)
            if not enabled.get(engine.id, False):
                skipped.append((path.name, "disabled in config"))
                continue
            if not engine.available():
                skipped.append((path.name, "model files or dependencies unavailable"))
                continue
            engines[engine.id] = engine
        except Exception as exc:
            skipped.append((path.name, str(exc)[:200]))
    return engines, skipped
