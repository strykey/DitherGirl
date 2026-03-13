import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def apply_sharpen(image: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    pil = Image.fromarray(image)
    enhanced = ImageEnhance.Sharpness(pil).enhance(1.0 + intensity)
    return np.array(enhanced)


def apply_blur(image: np.ndarray, radius: float = 1.0) -> np.ndarray:
    pil = Image.fromarray(image)
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(blurred)


def apply_chromatic_aberration(image: np.ndarray, shift: int = 3) -> np.ndarray:
    if len(image.shape) < 3 or image.shape[2] < 3:
        return image
    result = image.copy()
    result[:, shift:, 0] = image[:, :-shift, 0]
    result[:, :-shift, 2] = image[:, shift:, 2]
    return result


def apply_jpeg_glitch(image: np.ndarray, quality: int = 20) -> np.ndarray:
    import io
    pil = Image.fromarray(image)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=max(1, min(95, quality)))
    buf.seek(0)
    return np.array(Image.open(buf).convert("RGB"))


def apply_grain(image: np.ndarray, intensity: float = 20.0) -> np.ndarray:
    noise = np.random.normal(0, intensity, image.shape).astype(np.int16)
    return np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def apply_vignette(image: np.ndarray, strength: float = 0.5) -> np.ndarray:
    h, w = image.shape[:2]
    cx, cy = w / 2, h / 2
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    dist = np.sqrt(((x_coords - cx) / cx) ** 2 + ((y_coords - cy) / cy) ** 2)
    vignette = 1 - np.clip(dist * strength, 0, 1)
    result = (image.astype(np.float32) * vignette[:, :, np.newaxis]).astype(np.uint8)
    return result


def apply_glow(image: np.ndarray, radius: float = 10.0) -> np.ndarray:
    """Add a simple halo glow by blending a blurred copy back over the image.

    *radius* controls the blur radius – larger values produce a broader glow.
    The original and blurred images are blended evenly to create the halo.
    """
    pil = Image.fromarray(image)
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=radius))
    # blend 50/50; we could scale by radius if desired but simplest is fixed mix
    out = Image.blend(pil, blurred, alpha=0.5)
    return np.array(out)


EFFECT_REGISTRY = {
    "sharpen": apply_sharpen,
    "blur": apply_blur,
    "chromatic_aberration": apply_chromatic_aberration,
    "jpeg_glitch": apply_jpeg_glitch,
    "grain": apply_grain,
    "vignette": apply_vignette,
    "glow": apply_glow,
}

EFFECT_META = {
    "sharpen": {"label": "Sharpen", "param": "intensity", "min": 0.1, "max": 5.0, "default": 1.5, "phase": "pre"},
    "blur": {"label": "Blur", "param": "radius", "min": 0.5, "max": 8.0, "default": 1.0, "phase": "pre"},
    "chromatic_aberration": {"label": "Chromatic Aberration", "param": "shift", "min": 1, "max": 20, "default": 3, "phase": "post"},
    "jpeg_glitch": {"label": "JPEG Glitch", "param": "quality", "min": 1, "max": 50, "default": 20, "phase": "post"},
    "grain": {"label": "Grain", "param": "intensity", "min": 1.0, "max": 80.0, "default": 20.0, "phase": "post"},
    "vignette": {"label": "Vignette", "param": "strength", "min": 0.1, "max": 2.0, "default": 0.5, "phase": "post"},
    "glow":     {"label": "Glow",     "param": "radius",   "min": 1.0, "max": 50.0, "default": 10.0, "phase": "post"},
}


class EffectsPipeline:
    def __init__(self):
        self.effects = []

    def add_effect(self, effect_id: str, enabled: bool = True, param_value=None):
        meta = EFFECT_META.get(effect_id, {})
        self.effects.append({
            "id": effect_id,
            "enabled": enabled,
            "param": param_value if param_value is not None else meta.get("default", 1.0)
        })

    def apply_pre(self, image: np.ndarray) -> np.ndarray:
        return self._apply_phase(image, "pre")

    def apply_post(self, image: np.ndarray) -> np.ndarray:
        return self._apply_phase(image, "post")

    def _apply_phase(self, image: np.ndarray, phase: str) -> np.ndarray:
        result = image.copy()
        for effect in self.effects:
            if not effect["enabled"]:
                continue
            meta = EFFECT_META.get(effect["id"], {})
            if meta.get("phase") != phase:
                continue
            fn = EFFECT_REGISTRY.get(effect["id"])
            if fn:
                param_name = meta.get("param", "intensity")
                result = fn(result, **{param_name: effect["param"]})
        return result
