from __future__ import annotations
import json
from pathlib import Path
from time import perf_counter

from PIL import Image

from image_processing.processor import (
    adjust_brightness,
    adjust_contrast,
    resize_image,
    get_info,
)

def _timed(label: str, fn, *args, **kwargs):
    t0 = perf_counter()
    result = fn(*args, **kwargs)
    dt = perf_counter() - t0
    return dt, result

def run_bench(image_path: str, out_dir: str = "output/perf"):
    img_path = Path(image_path)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    results = []

    dt_load, img = _timed("load_image", Image.open, img_path)
    results.append({"op": "load_image", "seconds": dt_load})

    dt_info, info = _timed("get_info", get_info, img)
    results.append({"op": "get_info", "seconds": dt_info, "info": info})

    dt_bri, img_bri = _timed("adjust_brightness", adjust_brightness, img, 1.2)
    results.append({"op": "adjust_brightness", "seconds": dt_bri})

    dt_con, img_con = _timed("adjust_contrast", adjust_contrast, img_bri, 1.3)
    results.append({"op": "adjust_contrast", "seconds": dt_con})

    dt_res, img_res = _timed("resize", resize_image, img_con, 800, 600)
    results.append({"op": "resize", "seconds": dt_res})

    out_file = out / "perf_result.png"
    dt_save, _ = _timed("save_as", img_res.save, out_file, "PNG")
    results.append({"op": "save_as", "seconds": dt_save, "path": str(out_file)})

    (out / "perf.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("Wrote:", out / "perf.json")

if __name__ == "__main__":
    run_bench("tests/data/sample.jpg")
