from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QSizePolicy,
    QMessageBox,
    QComboBox,
    QInputDialog,
    QGroupBox,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QRect
import os
import glob
import json

from src.ui.img_label import ImageLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Annotation Tool")
        self.setGeometry(100, 100, 1000, 600)

        # Değiştirildi: QLabel yerine özel ImageLabel sınıfını kullanıyoruz
        self.image_label = ImageLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )  # Klavye odağı alabilsin

        # Sınıf yönetimi için bileşenler
        self.class_group = QGroupBox("Classes")
        self.class_layout = QVBoxLayout()

        # Sınıf listesi
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_selected)

        # Yeni sınıf ekleme butonu
        self.add_class_button = QPushButton("Add Class")
        self.add_class_button.clicked.connect(self.add_new_class)

        # Seçili dikdörtgenin sınıfını değiştirme butonu
        self.set_class_button = QPushButton("Set Class to Selected")
        self.set_class_button.clicked.connect(self.set_class_to_selected)

        # Sınıf yönetimi düzenine ekle
        self.class_layout.addWidget(QLabel("Select Class:"))
        self.class_layout.addWidget(self.class_combo)
        self.class_layout.addWidget(self.add_class_button)
        self.class_layout.addWidget(self.set_class_button)
        self.class_group.setLayout(self.class_layout)

        # Navigasyon butonları
        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_image)

        self.previous_button = QPushButton("Previous", self)
        self.previous_button.clicked.connect(self.show_previous_image)

        self.open_folder_button = QPushButton("Open Folder", self)
        self.open_folder_button.clicked.connect(self.open_folder)

        self.save_button = QPushButton("Save Annotations", self)
        self.save_button.clicked.connect(
            lambda: self.save_annotations(self.output_format)
        )
        self.clear_button = QPushButton("Clear Rectangles", self)
        self.clear_button.clicked.connect(self.clear_rectangles)

        # Ana düzen
        layout = QHBoxLayout()

        # Butonlar için dikey düzen
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.previous_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.open_folder_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.class_group)

        # MainWindow __init__ fonksiyonuna ekleyin:
        # Format seçim düğmesi
        self.format_group = QGroupBox("Output Format")
        self.format_layout = QVBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItem("YOLO Format")
        self.format_combo.addItem("Standard Format")
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)

        self.format_layout.addWidget(QLabel("Select Format:"))
        self.format_layout.addWidget(self.format_combo)
        self.format_group.setLayout(self.format_layout)

        # Bu düğmeyi butonlar düzenine ekleyin
        button_layout.addWidget(self.format_group)

        # Format değişkeni
        self.output_format = "yolo"  # Varsayılan format

        # Ana düzene butonları ve resim etiketini ekleyelim
        layout.addWidget(self.image_label, 1)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.image_paths = []
        self.current_index = 0
        self.annotations = {}  # Her resim için dikdörtgenleri saklayacak sözlük
        self.output_dir = ""  # Annotations klasörü

        # Sınıf yönetimi için değişkenler
        self.class_names = ["default"]  # En az bir sınıf olmalı
        self.update_class_combo()

        # Sınıf bilgilerini saklayacak dosya
        self.classes_file = ""
        # Yeni metod ekleyin

    def on_format_changed(self, index):
        """Format değiştiğinde çağrılır"""
        if index == 0:
            self.output_format = "yolo"
        else:
            self.output_format = "standard"

    def keyPressEvent(self, event):
        # Yön tuşları ile resimler arasında gezinme
        if event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Down:
            self.show_next_image()
        elif event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_Up:
            self.show_previous_image()
        else:
            super().keyPressEvent(event)

    def update_class_combo(self):
        """Sınıf combobox'ını günceller"""
        self.class_combo.clear()
        for class_name in self.class_names:
            self.class_combo.addItem(class_name)

    def get_selected_class_id(self):
        """Şu anda seçili olan sınıfın ID'sini döndürür"""
        return self.class_combo.currentIndex()

    def get_class_name(self, class_id):
        """Sınıf ID'sine göre sınıf adını döndürür"""
        if 0 <= class_id < len(self.class_names):
            return self.class_names[class_id]
        return "unknown"

    def show_selected_class(self, class_id):
        """Verilen sınıfı combo box'ta seçer"""
        if 0 <= class_id < len(self.class_names):
            self.class_combo.setCurrentIndex(class_id)

    def on_class_selected(self, index):
        """Sınıf seçildiğinde çağrılır"""
        if self.image_label.selected_rect_index >= 0:
            # Seçili dikdörtgen varsa, sınıfını güncelle
            self.image_label.set_rect_class(index)

    def add_new_class(self):
        """Yeni sınıf ekler"""
        class_name, ok = QInputDialog.getText(self, "Add Class", "Class name:")
        if ok and class_name:
            self.class_names.append(class_name)
            self.update_class_combo()
            # Yeni eklenen sınıfı seç
            self.class_combo.setCurrentIndex(len(self.class_names) - 1)

    def set_class_to_selected(self):
        """Seçili dikdörtgenin sınıfını değiştirir"""
        if self.image_label.selected_rect_index >= 0:
            class_id = self.class_combo.currentIndex()
            self.image_label.set_rect_class(class_id)

    def load_images(self, folder_path):
        image_extensions = [
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.bmp",
            "*.gif",
            "*.JPG",
            "*.JPEG",
            "*.PNG",
        ]
        self.image_paths = []
        for ext in image_extensions:
            self.image_paths.extend(glob.glob(os.path.join(folder_path, ext)))

        # Annotations klasörünü oluştur
        self.output_dir = os.path.join(folder_path, "annotations")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Sınıf bilgilerini saklayacak dosyayı belirle
        self.classes_file = os.path.join(self.output_dir, "classes.json")

        # Sınıf bilgilerini yükle
        self.load_classes()

        print(f"Bulunan resim sayısı: {len(self.image_paths)}")
        if self.image_paths:
            print(f"İlk resim: {self.image_paths[0]}")
            # Annotations sözlüğünü başlat
            self.annotations = {}
            for img_path in self.image_paths:
                self.annotations[img_path] = []

            # Mevcut dosyalardan annotations yükleme
            self.load_existing_annotations()

            self.current_index = 0
            self.display_image()
        else:
            print(f"Klasörde resim bulunamadı: {folder_path}")
            self.image_label.setText("Klasörde resim bulunamadı!")

    def load_classes(self):
        """Sınıf bilgilerini yükler"""
        if os.path.exists(self.classes_file):
            try:
                with open(self.classes_file, "r") as f:
                    self.class_names = json.load(f)
                    if not self.class_names:  # Boş liste kontrolü
                        self.class_names = ["default"]
                    self.update_class_combo()
                    print(f"Sınıflar yüklendi: {self.class_names}")
            except Exception as e:
                print(f"Sınıfları yüklerken hata: {e}")
                self.class_names = ["default"]
        else:
            # Varsayılan sınıfları kullan
            self.class_names = ["default"]
            self.update_class_combo()

    def save_classes(self):
        """Sınıf bilgilerini kaydeder"""
        try:
            with open(self.classes_file, "w") as f:
                json.dump(self.class_names, f)
                print(f"Sınıflar kaydedildi: {self.class_names}")
        except Exception as e:
            print(f"Sınıfları kaydederken hata: {e}")

    def load_existing_annotations(self):
        """Mevcut annotation dosyalarını yükler"""
        for img_path in self.image_paths:
            # Resim adından txt dosya adı oluştur
            img_name = os.path.basename(img_path)
            img_name_without_ext = os.path.splitext(img_name)[0]
            txt_path = os.path.join(self.output_dir, f"{img_name_without_ext}.txt")

            if os.path.exists(txt_path):
                # Resim boyutlarını al (YOLO formatını dönüştürmek için)
                pixmap = QPixmap(img_path)
                img_width = pixmap.width()
                img_height = pixmap.height()

                with open(txt_path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            parts = line.strip().split()

                            if len(parts) == 5:
                                # Muhtemelen YOLO veya standart format olabilir
                                if (
                                    0 < float(parts[1]) < 1
                                    and 0 < float(parts[2]) < 1
                                    and 0 < float(parts[3]) < 1
                                    and 0 < float(parts[4]) < 1
                                ):
                                    # YOLO formatı: class_id, x_center_norm, y_center_norm, w_norm, h_norm
                                    class_id = int(parts[0])
                                    x_center_norm = float(parts[1])
                                    y_center_norm = float(parts[2])
                                    w_norm = float(parts[3])
                                    h_norm = float(parts[4])

                                    # Normalize edilmiş koordinatları piksel değerlerine dönüştür
                                    x_center = x_center_norm * img_width
                                    y_center = y_center_norm * img_height
                                    w = w_norm * img_width
                                    h = h_norm * img_height

                                    # Sol üst köşe koordinatlarını hesapla
                                    x = int(x_center - w / 2)
                                    y = int(y_center - h / 2)
                                    w, h = int(w), int(h)

                                    self.annotations[img_path].append(
                                        (x, y, w, h, class_id)
                                    )
                                else:
                                    # Standart format: x, y, w, h, class_id
                                    x, y, w, h, class_id = map(int, parts)
                                    self.annotations[img_path].append(
                                        (x, y, w, h, class_id)
                                    )
                            elif len(parts) == 4:  # x y w h (eski format, sınıfsız)
                                x, y, w, h = map(int, parts)
                                class_id = 0  # Varsayılan sınıf
                                self.annotations[img_path].append(
                                    (x, y, w, h, class_id)
                                )
                            else:
                                print(f"Geçersiz satır formatı: {line}")
                                continue
                        except Exception as e:
                            print(f"Satır ayrıştırılırken hata: {line}, {e}")

    def display_image(self):
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            print(f"Görüntülenen resim: {current_image}")

            # Orijinal resim
            original_pixmap = QPixmap(current_image)
            if original_pixmap.isNull():
                print(f"Resim yüklenemedi: {current_image}")
                self.image_label.setText(
                    f"Resim yüklenemedi: {os.path.basename(current_image)}"
                )
                return

            # Orijinal resim boyutları
            orig_width = original_pixmap.width()
            orig_height = original_pixmap.height()

            # QLabel'ın boyutları
            label_width = self.image_label.width()
            label_height = self.image_label.height()

            # Resmi QLabel boyutlarına uygun şekilde ölçeklendirelim
            scaled_pixmap = original_pixmap.scaled(
                label_width,
                label_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Ölçeklendirilmiş resim boyutları
            scaled_width = scaled_pixmap.width()
            scaled_height = scaled_pixmap.height()

            # Önemli: Resmin QLabel içindeki gerçek konumunu hesapla
            # QLabel içinde merkezi hizalamada resim kenarlarında boşluk olabilir
            offset_x = (label_width - scaled_width) // 2
            offset_y = (label_height - scaled_height) // 2

            # Bu offset değerlerini ImageLabel sınıfına bildir
            self.image_label.offset_x = offset_x
            self.image_label.offset_y = offset_y

            # Orijinal ve ölçeklenmiş boyutları da kaydet
            self.image_label.orig_width = orig_width
            self.image_label.orig_height = orig_height
            self.image_label.scaled_width = scaled_width
            self.image_label.scaled_height = scaled_height

            # Pixmapı ayarla
            self.image_label.setPixmap(scaled_pixmap)

            # Debug bilgisi
            print(f"Orijinal boyutlar: {orig_width}x{orig_height}")
            print(f"Ölçeklenmiş boyutlar: {scaled_width}x{scaled_height}")
            print(f"Offset: {offset_x}, {offset_y}")

            # Mevcut resmin dikdörtgenlerini göster
            self.image_label.clearRectangles()
            if current_image in self.annotations:
                for annotation in self.annotations[current_image]:
                    if len(annotation) == 5:  # x, y, w, h, class_id
                        orig_x, orig_y, orig_w, orig_h, class_id = annotation
                    else:  # Eski format, sınıfsız
                        orig_x, orig_y, orig_w, orig_h = annotation
                        class_id = 0  # Varsayılan sınıf

                    # Orijinal koordinatları gösterilen resim boyutlarına ölçekle
                    # Orijinal koordinatlar -> Ölçeklenmiş koordinatlar
                    scale_x = scaled_width / orig_width
                    scale_y = scaled_height / orig_height

                    # Önemli: Offset'i ekle
                    x = int(orig_x * scale_x) + offset_x
                    y = int(orig_y * scale_y) + offset_y
                    w = int(orig_w * scale_x)
                    h = int(orig_h * scale_y)

                    rect = QRect(x, y, w, h)
                    self.image_label.rectangles.append(rect)
                    self.image_label.rectangle_classes.append(class_id)

            # Başlığa dosya adını ekleyelim
            self.setWindowTitle(f"Image Viewer - {os.path.basename(current_image)}")

    def show_next_image(self):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.display_image()

    def show_previous_image(self):
        if self.image_paths:
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.display_image()

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.load_images(folder_path)

    def add_rectangle_to_current_image(self, rect, class_id=0):
        """Geçerli resme çizilen dikdörtgeni annotations sözlüğüne ekler"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]

            # Görüntülenen dikdörtgenin gerçek koordinatlarını al
            # QLabel içindeki offseti çıkar
            display_x = rect.x() - self.image_label.offset_x
            display_y = rect.y() - self.image_label.offset_y
            display_w = rect.width()
            display_h = rect.height()

            # Ölçekleme oranları
            scale_x = self.image_label.orig_width / self.image_label.scaled_width
            scale_y = self.image_label.orig_height / self.image_label.scaled_height

            # Gösterilen koordinatları orijinal resim koordinatlarına çevir
            orig_x = int(display_x * scale_x)
            orig_y = int(display_y * scale_y)
            orig_w = int(display_w * scale_x)
            orig_h = int(display_h * scale_y)

            # Sınırları kontrol et
            orig_x = max(0, min(orig_x, self.image_label.orig_width - 1))
            orig_y = max(0, min(orig_y, self.image_label.orig_height - 1))
            orig_w = min(orig_w, self.image_label.orig_width - orig_x)
            orig_h = min(orig_h, self.image_label.orig_height - orig_y)

            # Kaydet
            self.annotations[current_image].append(
                (orig_x, orig_y, orig_w, orig_h, class_id)
            )
            print(
                f"Dikdörtgen eklendi (orijinal): x={orig_x}, y={orig_y}, w={orig_w}, h={orig_h}, class_id={class_id}"
            )
            print(
                f"Ölçekleme faktörleri: {scale_x:.3f}x, {scale_y:.3f}y, Offset: {self.image_label.offset_x}, {self.image_label.offset_y}"
            )

    def update_rectangle(self, index, rect, class_id=0):
        """Mevcut bir dikdörtgeni günceller"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            if current_image in self.annotations and 0 <= index < len(
                self.annotations[current_image]
            ):
                # Görüntülenen dikdörtgenin gerçek koordinatlarını al
                # QLabel içindeki offseti çıkar
                display_x = rect.x() - self.image_label.offset_x
                display_y = rect.y() - self.image_label.offset_y
                display_w = rect.width()
                display_h = rect.height()

                # Ölçekleme oranları
                scale_x = self.image_label.orig_width / self.image_label.scaled_width
                scale_y = self.image_label.orig_height / self.image_label.scaled_height

                # Gösterilen koordinatları orijinal resim koordinatlarına çevir
                orig_x = int(display_x * scale_x)
                orig_y = int(display_y * scale_y)
                orig_w = int(display_w * scale_x)
                orig_h = int(display_h * scale_y)

                # Sınırları kontrol et
                orig_x = max(0, min(orig_x, self.image_label.orig_width - 1))
                orig_y = max(0, min(orig_y, self.image_label.orig_height - 1))
                orig_w = min(orig_w, self.image_label.orig_width - orig_x)
                orig_h = min(orig_h, self.image_label.orig_height - orig_y)

                # Güncelle
                self.annotations[current_image][index] = (
                    orig_x,
                    orig_y,
                    orig_w,
                    orig_h,
                    class_id,
                )
                print(
                    f"Dikdörtgen güncellendi (orijinal): x={orig_x}, y={orig_y}, w={orig_w}, h={orig_h}, class_id={class_id}"
                )
                print(
                    f"Ölçekleme faktörleri: {scale_x:.3f}x, {scale_y:.3f}y, Offset: {self.image_label.offset_x}, {self.image_label.offset_y}"
                )

    def delete_rectangle(self, index):
        """Seçili dikdörtgeni siler"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            if current_image in self.annotations and 0 <= index < len(
                self.annotations[current_image]
            ):
                self.annotations[current_image].pop(index)
                print(f"Dikdörtgen silindi: indeks {index}")

    def save_annotations(self, format="yolo"):
        """Tüm annotationları txt dosyalarına kaydeder"""
        if not self.image_paths:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek görüntü yok!")
            return

        # Önce sınıfları kaydet
        self.save_classes()

        # Sonra annotationları kaydet
        for img_path, annotations in self.annotations.items():
            if not annotations:
                continue

            img_name = os.path.basename(img_path)
            img_name_without_ext = os.path.splitext(img_name)[0]
            txt_path = os.path.join(self.output_dir, f"{img_name_without_ext}.txt")

            # Resim boyutlarını al (YOLO formatı için gerekli)
            pixmap = QPixmap(img_path)
            img_width = pixmap.width()
            img_height = pixmap.height()

            # Hata ayıklama
            print(f"Resim boyutları: {img_width}x{img_height} - {img_path}")

            with open(txt_path, "w") as f:
                for annotation in annotations:
                    if len(annotation) == 5:  # x, y, w, h, class_id
                        x, y, w, h, class_id = annotation

                        if format == "yolo":
                            # YOLO format: <class_id> <x_center> <y_center> <width> <height> (normalize)
                            # Piksel koordinatları hesapla
                            x_center = x + w / 2
                            y_center = y + h / 2

                            # Normalize - Düzeltme yapıldı
                            # Koordinatların resim boyutlarını geçmediğinden emin ol
                            x_center = min(max(0, x_center), img_width)
                            y_center = min(max(0, y_center), img_height)

                            x_center_norm = x_center / img_width
                            y_center_norm = y_center / img_height
                            w_norm = w / img_width
                            h_norm = h / img_height

                            # Debug yazdırma
                            print(f"Orijinal: x={x}, y={y}, w={w}, h={h}")
                            print(f"Merkez: x_center={x_center}, y_center={y_center}")
                            print(
                                f"Normalize: x_norm={x_center_norm}, y_norm={y_center_norm}, w_norm={w_norm}, h_norm={h_norm}"
                            )

                            f.write(
                                f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n"
                            )
                        else:
                            # Standart format: x y w h class_id
                            f.write(f"{x} {y} {w} {h} {class_id}\n")
                    elif len(annotation) == 4:  # Eski format, sınıfsız
                        x, y, w, h = annotation
                        class_id = 0  # Varsayılan sınıf

                        if format == "yolo":
                            # YOLO format
                            x_center = x + w / 2
                            y_center = y + h / 2

                            # Normalize - Düzeltme yapıldı
                            x_center = min(max(0, x_center), img_width)
                            y_center = min(max(0, y_center), img_height)

                            x_center_norm = x_center / img_width
                            y_center_norm = y_center / img_height
                            w_norm = w / img_width
                            h_norm = h / img_height

                            f.write(
                                f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n"
                            )
                        else:
                            f.write(f"{x} {y} {w} {h} {class_id}\n")

        format_name = "YOLO" if format == "yolo" else "standart"
        QMessageBox.information(
            self,
            "Bilgi",
            f"Annotationlar {self.output_dir} klasörüne {format_name} formatında kaydedildi!",
        )

    def clear_rectangles(self):
        """Geçerli resmin dikdörtgenlerini temizler"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            self.annotations[current_image] = []
            self.image_label.clearRectangles()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "image_paths") and self.image_paths:
            self.display_image()
