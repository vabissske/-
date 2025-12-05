
import os
import pytest
from image_processor.processor import ImageProcessor
from PIL import Image

def ensure_image(path, size=(100,100), color=(255,0,0,255)):
    img = Image.new("RGBA", size, color)
    img.save(path)

def test_load_and_info(tmp_path):
    p = ImageProcessor(history_path=str(tmp_path/"history.json"))
    path = tmp_path/"i1.png"
    ensure_image(str(path))
    p.load(str(path))
    info = p.info()
    assert info['width'] == 100 and info['height'] == 100

def test_resize(tmp_path):
    p = ImageProcessor(history_path=str(tmp_path/"history.json"))
    path = tmp_path/"i2.png"
    ensure_image(str(path), size=(200,150))
    p.load(str(path))
    p.resize(50,50)
    assert p.info()['width'] == 50 and p.info()['height'] == 50

def test_brightness_contrast(tmp_path):
    p = ImageProcessor(history_path=str(tmp_path/"history.json"))
    path = tmp_path/"i3.png"
    ensure_image(str(path))
    p.load(str(path))
    p.brightness(0.5)
    p.contrast(1.5)
    assert p.image is not None

def test_save_and_format(tmp_path):
    p = ImageProcessor(history_path=str(tmp_path/"history.json"))
    path = tmp_path/"i4.png"
    ensure_image(str(path))
    p.load(str(path))
    out = tmp_path/"out.jpg"
    p.save(str(out), fmt='JPEG')
    assert out.exists()

def test_undo(tmp_path):
    p = ImageProcessor(history_path=str(tmp_path/"history.json"))
    path = tmp_path/"i5.png"
    ensure_image(str(path))
    p.load(str(path))
    p.resize(10,10)
    assert p.info()['width'] == 10
    ok = p.undo()
    assert ok
