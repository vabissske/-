
import sys, os, logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QSlider, QGroupBox, QFormLayout, QLineEdit, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from image_processor.processor import ImageProcessor

# Setup logging
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, "app.log"),
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setAcceptDrops(True)

    def set_pixmap_from_pil(self, pil_image):
        if pil_image is None:
            self.clear()
            return
        data = pil_image.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)
        self.setPixmap(pix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        if self.pixmap():
            self.setPixmap(self.pixmap().scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.parent().load_image(path)

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processor — Project 1")
        self.processor = ImageProcessor(history_path=os.path.join(os.getcwd(), "configs", "history.json"))

        self.init_ui()
        self._current_preview_path = None

    def init_ui(self):
        load_btn = QPushButton("Загрузить")
        load_btn.clicked.connect(self.on_load)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.on_save)

        undo_btn = QPushButton("Отменить (1 шаг)")
        undo_btn.clicked.connect(self.on_undo)

        # Image display
        self.orig_label = ImageLabel()
        self.orig_label.setFixedSize(350, 250)
        self.proc_label = ImageLabel()
        self.proc_label.setFixedSize(350, 250)

        # Controls: brightness, contrast, resize
        controls = QGroupBox("Параметры")
        form = QFormLayout()
        self.brightness_slider = QSlider(Qt.Horizontal); self.brightness_slider.setMinimum(1); self.brightness_slider.setMaximum(300); self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_preview_change)
        self.contrast_slider = QSlider(Qt.Horizontal); self.contrast_slider.setMinimum(1); self.contrast_slider.setMaximum(300); self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.on_preview_change)

        self.width_edit = QLineEdit(); self.height_edit = QLineEdit()
        self.width_edit.setPlaceholderText("ширина")
        self.height_edit.setPlaceholderText("высота")

        form.addRow("Яркость ( % )", self.brightness_slider)
        form.addRow("Контраст ( % )", self.contrast_slider)
        sz_box = QHBoxLayout()
        sz_box.addWidget(self.width_edit); sz_box.addWidget(self.height_edit)
        form.addRow("Изменить размер (px)", sz_box)

        controls.setLayout(form)

        # Info display
        self.info_label = QLabel("Информация об изображении:")

        # Layout composition
        btns = QHBoxLayout(); btns.addWidget(load_btn); btns.addWidget(save_btn); btns.addWidget(undo_btn)
        images = QHBoxLayout(); images.addWidget(self.orig_label); images.addWidget(self.proc_label)
        main = QVBoxLayout(); main.addLayout(btns); main.addLayout(images); main.addWidget(controls); main.addWidget(self.info_label)

        self.setLayout(main)
        self.setMinimumSize(800, 600)

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", filter="Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)")
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            self.processor.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            logging.exception("Failed to load image")
            return
        logging.info(f"Loaded image {path}")
        # show original
        self.orig_label.setPixmap(QPixmap(path).scaled(self.orig_label.width(), self.orig_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.update_info()
        self.update_preview()

    def on_save(self):
        default = os.path.join(os.getcwd(), "output", "processed.png")
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", default, filter="PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)")
        if path:
            try:
                # apply current settings before save
                self.apply_operations_to_processor()
                self.processor.save(path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка при сохранении", str(e))
                logging.exception("Save failed")
                return
            QMessageBox.information(self, "Сохранено", f"Файл сохранён: {path}")
            logging.info(f"Saved image to {path}")

    def on_undo(self):
        ok = self.processor.undo()
        if ok:
            self.update_preview()
            QMessageBox.information(self, "Отмена", "Отменено на 1 шаг")
        else:
            QMessageBox.information(self, "Отмена", "Нет операции для отмены")

    def update_info(self):
        info = self.processor.info()
        if not info:
            self.info_label.setText("Информация об изображении: нет")
        else:
            self.info_label.setText(f"Информация: {info.get('width')}x{info.get('height')}, режим {info.get('mode')}")

    def on_preview_change(self):
        # update preview live when sliders change
        if self.processor.image is None:
            return
        self.update_preview()

    def apply_operations_to_processor(self):
        # apply brightness/contrast/resize to processor.image (mutates)
        try:
            self.processor.load(self.processor.path)
        except Exception:
            pass
        b = self.brightness_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        # apply brightness then contrast
        self.processor.brightness(b)
        self.processor.contrast(c)
        # resize if provided
        w_text = self.width_edit.text().strip(); h_text = self.height_edit.text().strip()
        if w_text.isdigit() and h_text.isdigit():
            self.processor.resize(int(w_text), int(h_text))

    def update_preview(self):
        # create a temporary processed image for preview without overwriting original saved state
        if self.processor.image is None:
            return
        # Work on a copy
        from PIL import Image, ImageEnhance
        img = self.processor.image.copy()
        # apply current slider values
        b = self.brightness_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        img = ImageEnhance.Brightness(img).enhance(b)
        img = ImageEnhance.Contrast(img).enhance(c)
        # resize preview if requested
        w_text = self.width_edit.text().strip(); h_text = self.height_edit.text().strip()
        try:
            if w_text.isdigit() and h_text.isdigit():
                img = img.resize((int(w_text), int(h_text)))
        except Exception:
            pass
        # show processed preview in right label
        self.proc_label.set_pixmap_from_pil(img)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainUI()
    win.show()
    sys.exit(app.exec_())
