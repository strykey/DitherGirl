import base64
import io
import os
import numpy as np
from PIL import Image, ImageOps

from .algorithms import (
    ErrorDiffusionDitherer, OrderedDitherer, ModulationDitherer, SpecialDitherer,
    get_error_diffusion_info, get_ordered_info, MODULATION_INFO, SPECIAL_INFO
)
from .color import (
    get_all_built_in, load_palette_file, palette_to_numpy,
    extract_palette_from_image, save_custom_palette, hex_to_rgb
)
from .effects import EffectsPipeline, EFFECT_META
from .presets.manager import get_all_presets, save_preset, load_preset, delete_preset


ERROR_DIFFUSION_METHODS = list(get_error_diffusion_info().keys())
ORDERED_METHODS = list(get_ordered_info().keys()) + ["blue-noise"]
MODULATION_METHODS = list(MODULATION_INFO.keys())
SPECIAL_METHODS = list(SPECIAL_INFO.keys())


class DitherGirlAPI:
    def __init__(self):
        self._current_image = None
        self._current_path = None
        self._current_palette = None
        # keep two downscaled copies used for live preview; one for "fast"
        # algorithms (max 800px) and one for slow ones (max 300px).  Storing
        # them avoids recreating the same resize on every request.
        self._cached_fast = None
        self._cached_slow = None
        # last settings used for apply_dither and the resulting image data
        self._last_settings = None
        self._last_result = None

    def load_image(self, path: str) -> dict:
        try:
            pil = Image.open(path).convert("RGB")
            self._current_image = np.array(pil)
            self._current_path = path
            preview = self._image_to_base64(pil, max_size=1200)
            return {
                "ok": True,
                "width": pil.width,
                "height": pil.height,
                "filename": os.path.basename(path),
                "preview": preview
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def apply_dither(self, settings: dict, full_res: bool = False) -> dict:
        # return cached result if settings identical and not full resolution
        if not full_res and settings == self._last_settings and self._last_result is not None:
            return self._last_result

        if self._current_image is None:
            return {"ok": False, "error": "No image loaded"}

        try:
            palette_data = settings.get("palette")
            if palette_data and "rgb" in palette_data:
                palette_np = np.array(palette_data["rgb"], dtype=np.uint8)
            else:
                palette_np = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8)

            pipeline = EffectsPipeline()
            for fx in settings.get("effects", []):
                if fx.get("enabled"):
                    pipeline.add_effect(fx["id"], True, fx.get("param"))

            image = self._current_image.copy()

            brightness = float(settings.get("brightness", 0))
            contrast   = float(settings.get("contrast", 0))
            img_f = image.astype(np.float32)
            img_f = img_f + brightness
            img_f = (img_f - 127.5) * (1 + contrast / 100.0) + 127.5
            image = np.clip(img_f, 0, 255).astype(np.uint8)

            if settings.get("invert"):
                image = 255 - image

            # apply global threshold adjustment: a signed offset around 128
            thr = float(settings.get("threshold", 128)) - 128.0
            if thr != 0:
                img_t = image.astype(np.float32) + thr
                image = np.clip(img_t, 0, 255).astype(np.uint8)

            # apply depth/bit-depth posterization: reduce color depth to specified bits per channel
            depth = int(settings.get("depth", 8))
            if depth < 8:
                # posterize: shift right to reduce bits, then shift left to expand back to 0-255 range
                shift_amount = 8 - depth
                image = ((image >> shift_amount) << shift_amount).astype(np.uint8)

            # scale is a float now; values >1 downsample, <1 upsample
            scale = float(settings.get("scale", 1))
            # choose correct cached base image if available
            if not full_res and self._cached_fast is not None:
                # pick slow vs fast depending on algorithm
                algorithm = settings.get("algorithm", "floyd-steinberg")
                from .algorithms import ErrorDiffusionDitherer
                is_slow = algorithm in [
                    "floyd-steinberg","atkinson","jarvis-judice-ninke",
                    "stucki","burkes","sierra","sierra-two-row","sierra-lite"
                ]
                image = self._cached_slow.copy() if is_slow else self._cached_fast.copy()

            if scale > 1:
                h, w = image.shape[:2]
                image = np.array(Image.fromarray(image).resize(
                    (max(1, int(w / scale)), max(1, int(h / scale))), Image.LANCZOS
                ))
            elif scale > 0 and scale < 1:
                # enlarge before dithering to get smaller result pixels
                h, w = image.shape[:2]
                image = np.array(Image.fromarray(image).resize(
                    (max(1, int(w / scale)), max(1, int(h / scale))), Image.LANCZOS
                ))

            image = pipeline.apply_pre(image)

            algorithm  = settings.get("algorithm", "floyd-steinberg")
            serpentine = bool(settings.get("serpentine", False))
            ditherer   = self._build_ditherer(algorithm, settings)
            ditherer.serpentine = serpentine

            result = ditherer.apply(image, palette_np)
            result = pipeline.apply_post(result)

            if scale > 1:
                h2, w2 = image.shape[:2]
                result = np.array(Image.fromarray(result).resize(
                    (int(w2 * scale), int(h2 * scale)), Image.NEAREST
                ))
            elif scale > 0 and scale < 1:
                h2, w2 = image.shape[:2]
                result = np.array(Image.fromarray(result).resize(
                    (max(1, int(w2 * scale)), max(1, int(h2 * scale))), Image.NEAREST
                ))

            b64 = self._image_to_base64(Image.fromarray(result))
            resp = {"ok": True, "image": b64}
            # cache for identical future requests
            if not full_res:
                self._last_settings = settings.copy() if isinstance(settings, dict) else settings
                self._last_result = resp
            return resp

        except Exception as e:
            import traceback
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

    def export_image(self, path: str, settings: dict) -> dict:
        try:
            result = self.apply_dither(settings, full_res=True)
            if not result["ok"]:
                return result

            b64 = result["image"].split(",")[1] if "," in result["image"] else result["image"]
            img_bytes = base64.b64decode(b64)
            pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            scale = int(settings.get("export_scale", 1))
            if scale > 1:
                pil = pil.resize((pil.width * scale, pil.height * scale), Image.NEAREST)

            fmt = settings.get("format", "png").upper()
            quality = int(settings.get("quality", 90))
            save_kwargs = {}
            if fmt in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality

            pil.save(path, format=fmt, **save_kwargs)
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_palettes(self) -> list:
        return get_all_built_in()

    def load_palette(self, path: str) -> dict:
        try:
            palette = load_palette_file(path)
            return {"ok": True, "palette": palette}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def extract_palette(self, n_colors: int) -> dict:
        if self._current_image is None:
            return {"ok": False, "error": "No image loaded"}
        try:
            colors = extract_palette_from_image(self._current_image, n_colors)
            rgb = [hex_to_rgb(c) for c in colors]
            return {"ok": True, "colors": colors, "rgb": rgb}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_algorithms(self) -> dict:
        return {
            "error_diffusion": get_error_diffusion_info(),
            "ordered": get_ordered_info(),
            "modulation": MODULATION_INFO,
            "special": SPECIAL_INFO
        }

    def get_effects_meta(self) -> dict:
        return EFFECT_META

    def get_presets(self) -> list:
        return get_all_presets()

    def save_preset(self, name: str, settings: dict) -> dict:
        try:
            save_preset(name, settings)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def load_preset(self, preset_id: str) -> dict:
        data = load_preset(preset_id)
        if data:
            return {"ok": True, "preset": data}
        return {"ok": False, "error": "Preset not found"}

    def delete_preset(self, preset_id: str) -> dict:
        ok = delete_preset(preset_id)
        return {"ok": ok}

    def open_file_dialog(self) -> str:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            path = filedialog.askopenfilename(
                title="Open Image",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp *.gif"),
                    ("All files", "*.*")
                ]
            )
            root.destroy()
            return path or ""
        except Exception:
            try:
                import webview
                wins = webview.windows
                if wins:
                    result = wins[0].create_file_dialog(
                        webview.OPEN_DIALOG,
                        allow_multiple=False,
                        file_types=('Image files (*.jpg;*.jpeg;*.png;*.bmp;*.webp;*.gif)',)
                    )
                    return result[0] if result else ""
            except Exception:
                pass
            return ""

    def load_image_base64(self, b64: str, filename: str) -> dict:
        try:
            import base64 as b64mod
            import io as _io
            _, data = b64.split(',', 1) if ',' in b64 else ('', b64)
            img_bytes = b64mod.b64decode(data)
            pil = Image.open(_io.BytesIO(img_bytes)).convert("RGB")
            self._current_image = np.array(pil)
            self._current_path = filename
            # reset cache
            self._last_settings = None
            self._last_result = None
            self._cached_fast = self._make_cached(pil, max_dim=800)
            self._cached_slow = self._make_cached(pil, max_dim=300)
            preview = self._image_to_base64(pil, max_size=1200)
            return {
                "ok": True,
                "width": pil.width,
                "height": pil.height,
                "filename": filename,
                "preview": preview
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _build_ditherer(self, algorithm: str, settings: dict):
        if algorithm in ERROR_DIFFUSION_METHODS:
            return ErrorDiffusionDitherer(algorithm)
        elif algorithm in ORDERED_METHODS:
            d = OrderedDitherer(algorithm)
            # ordered dither may respect the global threshold
            try:
                d.threshold = float(settings.get("threshold", 128))
            except Exception:
                d.threshold = 128.0
            return d
        elif algorithm in MODULATION_METHODS:
            d = ModulationDitherer(algorithm)
            d.frequency = int(settings.get("depth", 4))
            return d
        elif algorithm in SPECIAL_METHODS:
            d = SpecialDitherer(algorithm)
            d.intensity = int(settings.get("depth", 64))
            return d
        return ErrorDiffusionDitherer("floyd-steinberg")

    def _image_to_base64(self, pil: Image.Image, max_size: int = None) -> str:
        if max_size:
            pil.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"