import json
import os
import numpy as np
from pathlib import Path


BUILT_IN_DIR = Path(__file__).parent / "built_in"


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def load_palette_file(path: str) -> dict:
    with open(path, "r") as f:
        data = json.load(f)
    colors_rgb = [hex_to_rgb(c) for c in data["colors"]]
    return {
        "name": data.get("name", "Custom"),
        "author": data.get("author", "Unknown"),
        "colors": data["colors"],
        "rgb": colors_rgb
    }


def get_all_built_in() -> list:
    palettes = []
    for path in sorted(BUILT_IN_DIR.glob("*.json")):
        try:
            p = load_palette_file(str(path))
            p["id"] = path.stem
            palettes.append(p)
        except Exception:
            continue
    return palettes


def palette_to_numpy(palette: dict) -> np.ndarray:
    return np.array(palette["rgb"], dtype=np.uint8)


def save_custom_palette(name: str, colors: list, path: str) -> bool:
    data = {"name": name, "author": "User", "colors": colors}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return True
