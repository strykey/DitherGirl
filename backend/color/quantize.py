import numpy as np
from PIL import Image


def median_cut(image: np.ndarray, n_colors: int) -> list:
    pixels = image.reshape(-1, 3).tolist()
    buckets = [pixels]

    while len(buckets) < n_colors:
        buckets.sort(key=lambda b: max(
            max(p[c] for p in b) - min(p[c] for p in b) for c in range(3)
        ), reverse=True)
        bucket = buckets.pop(0)
        channel = max(range(3), key=lambda c: max(p[c] for p in bucket) - min(p[c] for p in bucket))
        bucket.sort(key=lambda p: p[channel])
        mid = len(bucket) // 2
        buckets.append(bucket[:mid])
        buckets.append(bucket[mid:])

    palette = []
    for bucket in buckets:
        if bucket:
            avg = [int(sum(p[c] for p in bucket) / len(bucket)) for c in range(3)]
            palette.append(avg)

    return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]


def extract_palette_from_image(image_array: np.ndarray, n_colors: int = 8) -> list:
    pil = Image.fromarray(image_array)
    pil_small = pil.resize((150, 150), Image.LANCZOS)
    arr = np.array(pil_small.convert("RGB"))
    return median_cut(arr, n_colors)
