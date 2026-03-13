import numpy as np
from .base import BaseDitherer


def _nearest_vectorized(img: np.ndarray, palette: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    flat = img.reshape(-1, 3).astype(np.float32)
    pal  = palette.astype(np.float32)
    dists = np.sum((flat[:, None, :] - pal[None, :, :]) ** 2, axis=2)
    return pal[np.argmin(dists, axis=1)].astype(np.uint8).reshape(h, w, 3)


def _find_one(pixel: np.ndarray, palette: np.ndarray) -> np.ndarray:
    dists = np.sum((palette.astype(np.float32) - pixel.astype(np.float32)) ** 2, axis=1)
    return palette[np.argmin(dists)]


MODULATION_INFO = {
    "scanlines": "Horizontal scanline overlay — CRT monitor effect",
    "crosshatch": "Grid crosshatch pattern — printmaking aesthetic",
    "fm": "Frequency modulation — density-based dot pattern",
    "am": "Amplitude modulation — size-based dot pattern",
}


class ModulationDitherer(BaseDitherer):
    def __init__(self, method: str = "scanlines"):
        super().__init__()
        self.method    = method
        self.frequency = 4
        self.thickness = 1

    def apply(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        if self.method == "scanlines":  return self._scanlines(image, palette)
        if self.method == "crosshatch": return self._crosshatch(image, palette)
        if self.method == "fm":         return self._fm(image, palette)
        if self.method == "am":         return self._am(image, palette)
        return image

    def _scanlines(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        result = _nearest_vectorized(image, palette)
        freq   = max(1, self.frequency)
        black  = _find_one(np.array([0,0,0], dtype=np.uint8), palette)
        mask   = (np.arange(image.shape[0]) % freq) < self.thickness
        result[mask] = black
        return result

    def _crosshatch(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        result = _nearest_vectorized(image, palette)
        freq   = max(1, self.frequency)
        black  = _find_one(np.array([0,0,0], dtype=np.uint8), palette)
        h, w   = image.shape[:2]
        row_mask = (np.arange(h) % freq) < self.thickness
        col_mask = (np.arange(w) % freq) < self.thickness
        result[row_mask, :] = black
        result[:, col_mask] = black
        return result

    def _fm(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        h, w   = image.shape[:2]
        gray   = np.mean(image, axis=2) / 255.0
        black  = _find_one(np.array([0,0,0],   dtype=np.uint8), palette).astype(np.float32)
        white  = _find_one(np.array([255,255,255], dtype=np.uint8), palette).astype(np.float32)
        freq   = max(1, self.frequency) * 4
        ys, xs = np.mgrid[0:h, 0:w]
        phase  = (xs + ys * 0.5) % freq
        density = freq * gray
        mask   = phase < density
        result = np.where(mask[:, :, np.newaxis], white, black).astype(np.uint8)
        return result

    def _am(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        h, w   = image.shape[:2]
        gray   = np.mean(image, axis=2) / 255.0
        nearest = _nearest_vectorized(image, palette)
        black  = _find_one(np.array([0,0,0], dtype=np.uint8), palette)
        freq   = max(2, self.frequency)
        ys, xs = np.mgrid[0:h, 0:w]
        cx = (xs % freq) / freq - 0.5
        cy = (ys % freq) / freq - 0.5
        dist = np.sqrt(cx**2 + cy**2) * 2
        mask = dist < gray
        result = np.where(mask[:, :, np.newaxis], nearest, black)
        return result.astype(np.uint8)


SPECIAL_INFO = {
    "random": "Random threshold — raw noise, unpredictable texture",
    "glitch":  "Glitch dither — digital artifact aesthetic",
}


class SpecialDitherer(BaseDitherer):
    def __init__(self, method: str = "random"):
        super().__init__()
        self.method    = method
        self.intensity = 64

    def apply(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        if self.method == "random": return self._random(image, palette)
        if self.method == "glitch": return self._glitch(image, palette)
        return image

    def _random(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        noise  = np.random.randint(-self.intensity, self.intensity, image.shape, dtype=np.int16)
        noisy  = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return _nearest_vectorized(noisy, palette)

    def _glitch(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        h, w   = image.shape[:2]
        result = image.copy()
        rng    = np.random.default_rng()
        n      = max(1, h // 20)
        rows   = rng.integers(0, h, n)
        shifts = rng.integers(-w // 8, w // 8, n)
        for r, s in zip(rows, shifts):
            result[r] = np.roll(image[r], s, axis=0)
        noise  = np.random.randint(-self.intensity // 2, self.intensity // 2, result.shape, dtype=np.int16)
        result = np.clip(result.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return _nearest_vectorized(result, palette)