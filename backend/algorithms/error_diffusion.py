import numpy as np
from .base import BaseDitherer


MATRICES = {
    "floyd-steinberg": {
        "offsets": [(0, 1, 7/16), (1, -1, 3/16), (1, 0, 5/16), (1, 1, 1/16)],
        "description": "Classic error diffusion — balanced, widely used"
    },
    "atkinson": {
        "offsets": [(0, 1, 1/8), (0, 2, 1/8), (1, -1, 1/8), (1, 0, 1/8), (1, 1, 1/8), (2, 0, 1/8)],
        "description": "Apple Macintosh style — partial diffusion, sharp edges"
    },
    "jarvis-judice-ninke": {
        "offsets": [
            (0, 1, 7/48), (0, 2, 5/48),
            (1, -2, 3/48), (1, -1, 5/48), (1, 0, 7/48), (1, 1, 5/48), (1, 2, 3/48),
            (2, -2, 1/48), (2, -1, 3/48), (2, 0, 5/48), (2, 1, 3/48), (2, 2, 1/48)
        ],
        "description": "Wide diffusion matrix — smooth gradients, slight blur"
    },
    "stucki": {
        "offsets": [
            (0, 1, 8/42), (0, 2, 4/42),
            (1, -2, 2/42), (1, -1, 4/42), (1, 0, 8/42), (1, 1, 4/42), (1, 2, 2/42),
            (2, -2, 1/42), (2, -1, 2/42), (2, 0, 4/42), (2, 1, 2/42), (2, 2, 1/42)
        ],
        "description": "Stucki variant — sharper than JJN, excellent detail retention"
    },
    "burkes": {
        "offsets": [
            (0, 1, 8/32), (0, 2, 4/32),
            (1, -2, 2/32), (1, -1, 4/32), (1, 0, 8/32), (1, 1, 4/32), (1, 2, 2/32)
        ],
        "description": "Simplified Stucki — faster, similar quality"
    },
    "sierra": {
        "offsets": [
            (0, 1, 5/32), (0, 2, 3/32),
            (1, -2, 2/32), (1, -1, 4/32), (1, 0, 5/32), (1, 1, 4/32), (1, 2, 2/32),
            (2, -1, 2/32), (2, 0, 3/32), (2, 1, 2/32)
        ],
        "description": "Three-row diffusion — smooth tones, good for photos"
    },
    "sierra-two-row": {
        "offsets": [
            (0, 1, 4/16), (0, 2, 3/16),
            (1, -2, 1/16), (1, -1, 2/16), (1, 0, 3/16), (1, 1, 2/16), (1, 2, 1/16)
        ],
        "description": "Two-row variant of Sierra — balanced speed and quality"
    },
    "sierra-lite": {
        "offsets": [(0, 1, 2/4), (1, -1, 1/4), (1, 0, 1/4)],
        "description": "Minimal Sierra — fast, preserves texture well"
    }
}

PREVIEW_MAX = 512


def _nearest_palette_vectorized(pixels_flat: np.ndarray, palette: np.ndarray) -> np.ndarray:
    p = pixels_flat.astype(np.float32)
    pal = palette.astype(np.float32)
    dists = np.sum((p[:, None, :] - pal[None, :, :]) ** 2, axis=2)
    idx = np.argmin(dists, axis=1)
    return pal[idx].astype(np.uint8)


class ErrorDiffusionDitherer(BaseDitherer):
    def __init__(self, method: str = "floyd-steinberg"):
        super().__init__()
        self.method = method
        self.offsets = MATRICES[method]["offsets"]

    def apply(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        from PIL import Image as PILImage

        h, w = image.shape[:2]
        scale_down = max(1, max(h, w) // PREVIEW_MAX)

        if scale_down > 1:
            small = PILImage.fromarray(image).resize(
                (w // scale_down, h // scale_down), PILImage.LANCZOS
            )
            work = np.array(small, dtype=np.float32)
            result_small = self._diffuse(work, palette)
            result_big = PILImage.fromarray(result_small).resize(
                (w, h), PILImage.NEAREST
            )
            return np.array(result_big)

        return self._diffuse(image.astype(np.float32), palette)

    def _diffuse(self, img: np.ndarray, palette: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        result = np.zeros((h, w, 3), dtype=np.uint8)
        pal = palette.astype(np.float32)

        for y in range(h):
            ltr = (not self.serpentine) or (y % 2 == 0)
            xs = range(w) if ltr else range(w - 1, -1, -1)
            d = 1 if ltr else -1

            for x in xs:
                old = img[y, x].copy()
                dists = np.sum((pal - old) ** 2, axis=1)
                new = pal[np.argmin(dists)]
                result[y, x] = new.astype(np.uint8)
                err = old - new
                for dy, dx_off, w_coef in self.offsets:
                    nx = x + dx_off * d
                    ny = y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        img[ny, int(nx)] = np.clip(img[ny, int(nx)] + err * w_coef, 0, 255)

        return result


def get_error_diffusion_info():
    return {k: v["description"] for k, v in MATRICES.items()}