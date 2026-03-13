from abc import ABC, abstractmethod
import numpy as np
from PIL import Image


class BaseDitherer(ABC):
    def __init__(self):
        self.serpentine = False
        self.scale = 1

    @abstractmethod
    def apply(self, image: np.ndarray, palette: np.ndarray) -> np.ndarray:
        pass

    def find_nearest_color(self, pixel: np.ndarray, palette: np.ndarray) -> np.ndarray:
        deltas = palette.astype(np.float32) - pixel.astype(np.float32)
        distances = np.sum(deltas ** 2, axis=1)
        return palette[np.argmin(distances)]

    def find_nearest_color_batch(self, pixels: np.ndarray, palette: np.ndarray) -> np.ndarray:
        p = pixels.reshape(-1, pixels.shape[-1]).astype(np.float32)
        pal = palette.astype(np.float32)
        result = np.zeros_like(p)
        for i in range(len(p)):
            deltas = pal - p[i]
            distances = np.sum(deltas ** 2, axis=1)
            result[i] = pal[np.argmin(distances)]
        return result.reshape(pixels.shape).astype(np.uint8)

    def preprocess(self, image: np.ndarray, brightness: float, contrast: float) -> np.ndarray:
        img = image.astype(np.float32)
        img = img + brightness
        img = (img - 127.5) * (1 + contrast / 100.0) + 127.5
        return np.clip(img, 0, 255).astype(np.uint8)
