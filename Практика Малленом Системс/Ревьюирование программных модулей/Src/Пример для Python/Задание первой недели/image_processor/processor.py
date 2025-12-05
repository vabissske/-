
import os
import json
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance

class ImageProcessor:
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')

    def __init__(self, history_path=None):
        self.image = None
        self.prev_image = None
        self.path = None
        self.history_path = history_path or os.path.join(os.getcwd(), "configs", "history.json")
        # ensure history file exists
        if not os.path.exists(self.history_path):
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _record(self, operation, params=None):
        entry = {
            "date": datetime.now().isoformat(sep=' ', timespec='seconds'),
            "operation": operation,
            "params": params or {}
        }
        try:
            with open(self.history_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0); f.truncate()
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump([entry], f, ensure_ascii=False, indent=2)

    def load(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}")
        self.image = Image.open(path).convert("RGBA")
        self.prev_image = self.image.copy()
        self.path = path
        self._record("load", {"path": path})

    def save(self, path: str, fmt: str = None):
        if self.image is None:
            raise RuntimeError("No image loaded")
        save_kwargs = {}
        if fmt:
            fmt = fmt.upper()
            if fmt == 'JPG': fmt = 'JPEG'
            save_kwargs['format'] = fmt
        outdir = os.path.dirname(path)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        img = self.image.convert("RGB") if path.lower().endswith(('.jpg','.jpeg')) else self.image
        img.save(path, **save_kwargs)
        self._record("save", {"path": path, "format": fmt})

    def info(self):
        if self.image is None and self.path is None:
            return {}
        if self.image is None:
            img = Image.open(self.path)
        else:
            img = self.image
        return {"width": img.width, "height": img.height, "mode": img.mode}

    def resize(self, w: int, h: int):
        if self.image is None:
            raise RuntimeError("No image loaded")
        self.prev_image = self.image.copy()
        self.image = self.image.resize((w, h))
        self._record("resize", {"w": w, "h": h})

    def to_grayscale(self):
        if self.image is None:
            raise RuntimeError("No image loaded")
        self.prev_image = self.image.copy()
        self.image = self.image.convert("L").convert("RGBA")
        self._record("grayscale", {})

    def blur(self, radius: float = 1.0):
        if self.image is None:
            raise RuntimeError("No image loaded")
        self.prev_image = self.image.copy()
        self.image = self.image.filter(ImageFilter.GaussianBlur(radius))
        self._record("blur", {"radius": radius})

    def brightness(self, factor: float):
        if self.image is None:
            raise RuntimeError("No image loaded")
        self.prev_image = self.image.copy()
        enhancer = ImageEnhance.Brightness(self.image)
        self.image = enhancer.enhance(factor)
        self._record("brightness", {"factor": factor})

    def contrast(self, factor: float):
        if self.image is None:
            raise RuntimeError("No image loaded")
        self.prev_image = self.image.copy()
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(factor)
        self._record("contrast", {"factor": factor})

    def undo(self):
        if self.prev_image is None:
            return False
        self.image, self.prev_image = self.prev_image, None
        self._record("undo", {})
        return True
