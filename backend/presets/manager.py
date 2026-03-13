import json
import os
from pathlib import Path


PRESETS_DIR = Path.home() / ".dither-girl" / "presets"
BUILT_IN_DIR = Path(__file__).parent / "built_in"


def ensure_dirs():
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)


def get_all_presets() -> list:
    ensure_dirs()
    presets = []

    for path in sorted(BUILT_IN_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            data["id"] = path.stem
            data["built_in"] = True
            presets.append(data)
        except Exception:
            continue

    for path in sorted(PRESETS_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            data["id"] = path.stem
            data["built_in"] = False
            presets.append(data)
        except Exception:
            continue

    return presets


def save_preset(name: str, settings: dict) -> bool:
    ensure_dirs()
    safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    path = PRESETS_DIR / f"{safe_name}.json"
    data = {"name": name, "settings": settings}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return True


def load_preset(preset_id: str) -> dict:
    user_path = PRESETS_DIR / f"{preset_id}.json"
    built_in_path = BUILT_IN_DIR / f"{preset_id}.json"

    for path in [user_path, built_in_path]:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    return {}


def delete_preset(preset_id: str) -> bool:
    path = PRESETS_DIR / f"{preset_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
