import numpy as np
from .base import BaseDitherer


def _bayer_matrix(n: int) -> np.ndarray:
    if n == 1:
        return np.array([[0]])
    smaller = _bayer_matrix(n // 2)
    return np.bmat([
        [4 * smaller, 4 * smaller + 2],
        [4 * smaller + 3, 4 * smaller + 1]
    ]).A / (n * n)


BAYER_2  = _bayer_matrix(2)
BAYER_4  = _bayer_matrix(4)
BAYER_8  = _bayer_matrix(8)
BAYER_16 = _bayer_matrix(16)

CLUSTER_DOT_4 = np.array([
    [12, 5, 6, 13],
    [4, 0, 1, 7],
    [11, 3, 2, 8],
    [15, 10, 9, 14]
], dtype=np.float32) / 16.0

HALFTONE_8 = np.array([
    [24,10,12,26,35,47,49,37],
    [8, 0, 2,14,45,59,61,51],
    [22, 6, 4,16,43,57,63,53],
    [30,20,18,28,33,41,55,39],
    [34,46,48,36,25,11,13,27],
    [44,58,60,50, 9, 1, 3,15],
    [42,56,62,52,23, 7, 5,17],
    [32,40,54,38,31,21,19,29]
], dtype=np.float32) / 64.0


def _generate_blue_noise(size: int = 64) -> np.ndarray:
    rng = np.random.default_rng(42)
    noise = rng.random((size, size))
    try:
        from scipy.ndimage import gaussian_filter
        low = gaussian_filter(noise, sigma=2)
        high = noise - low
    except ImportError:
        high = noise - 0.5
    normalized = (high - high.min()) / (high.max() - high.min() + 1e-8)
    return normalized


_BLUE_NOISE_CACHE = None


def _get_blue_noise():
    global _BLUE_NOISE_CACHE
    if _BLUE_NOISE_CACHE is None:
        _BLUE_NOISE_CACHE = _generate_blue_noise(64)
    return _BLUE_NOISE_CACHE


ORDERED_CONFIGS = {
    "bayer-2x2":   {"matrix": BAYER_2,       "description": "2×2 Bayer — minimal, very pixelated"},
    "bayer-4x4":   {"matrix": BAYER_4,       "description": "4×4 Bayer — classic ordered look"},
    "bayer-8x8":   {"matrix": BAYER_8,       "description": "8×8 Bayer — smooth ordered dither"},
    "bayer-16x16": {"matrix": BAYER_16,      "description": "16×16 Bayer — very smooth, subtle pattern"},
    "cluster-dot": {"matrix": CLUSTER_DOT_4, "description": "Cluster dot — halftone newspaper look"},
    "halftone":    {"matrix": HALFTONE_8,    "description": "Halftone 8×8 — circular dot pattern"},
}


def _nearest_vectorized(img: np.ndarray, palette: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    flat = img.reshape(-1, 3).astype(np.float32)
    pal  = palette.astype(np.float32)
    dists = np.sum((flat[:, None, :] - pal[None, :, :]) ** 2, axis=2)
    idx = np.argmin(dists, axis=1)
    return pal[idx].astype(np.uint8).reshape(h, w, 3)


class OrderedDitherer(BaseDitherer):
    def __init__(self, method: str = "bayer-8x8"):
        super().__init__()
        self.method = method

    def apply(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        matrix = _get_blue_noise() if self.method == "blue-noise" \
            else ORDERED_CONFIGS[self.method]["matrix"]

        h, w = image.shape[:2]
        mh, mw = matrix.shape
        tiled = np.tile(matrix, (h // mh + 1, w // mw + 1))[:h, :w]
        threshold_map = ((tiled - 0.5) * 128).astype(np.float32)
        # incorporate user threshold by shifting the map up/down
        if hasattr(self, 'threshold'):
            threshold_map += (self.threshold - 128.0)

        adjusted = np.clip(
            image.astype(np.float32) + threshold_map[:, :, np.newaxis],
            0, 255
        ).astype(np.uint8)

        return _nearest_vectorized(adjusted, palette)


def get_ordered_info():
    info = {k: v["description"] for k, v in ORDERED_CONFIGS.items()}
    info["blue-noise"] = "Blue noise — organic irregular pattern, no visible structure"
    return info