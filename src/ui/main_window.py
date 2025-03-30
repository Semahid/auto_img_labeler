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
from src.ui.anotation_manager import AnnotationManager
from src.ui.rectangle_handler import RectangleHandler, ImageInfo

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

        # Annotation yöneticisini oluştur
        self.annotation_manager = AnnotationManager()

        # Dikdörtgen işleyicisini oluştur
        self.rectangle_handler = RectangleHandler(self.annotation_manager)
        
        # Resim bilgisi nesnesi
        self.image_info = ImageInfo()
        
        # Sınıf yönetimi için değişkenler
        self.class_names = ["default"]  # En az bir sınıf olmalı
        self.update_class_combo() 
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
            self.annotation_manager.class_names.append(class_name)
            self.class_names = self.annotation_manager.class_names
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

        print(f"Bulunan resim sayısı: {len(self.image_paths)}")
        if self.image_paths:
            print(f"İlk resim: {self.image_paths[0]}")
            
            # Annotation yöneticisini başlat
            self.annotation_manager.initialize(self.image_paths, self.output_dir)
            
            # Sınıf listesini güncelle
            self.class_names = self.annotation_manager.class_names
            self.update_class_combo()

            self.current_index = 0
            self.display_image()
        else:
            print(f"Klasörde resim bulunamadı: {folder_path}")
            self.image_label.setText("Klasörde resim bulunamadı!")

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

            # Bu değerleri ImageInfo'ya kaydet
            self.image_info.update(
                orig_width, orig_height, scaled_width, scaled_height, offset_x, offset_y
            )
            
            # ImageLabel'a da bildir (geriye uyumluluk için)
            self.image_label.offset_x = offset_x
            self.image_label.offset_y = offset_y
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
            
            # RectangleHandler'ı kullanarak dikdörtgenleri al
            display_rects, class_ids = self.rectangle_handler.get_rectangles_for_display(
                current_image, self.image_info
            )
            
            # Dikdörtgenleri ImageLabel'a ekle
            for i, rect in enumerate(display_rects):
                self.image_label.rectangles.append(rect)
                self.image_label.rectangle_classes.append(class_ids[i])
                print(f"Etiket eklendi: {rect}, class_id={class_ids[i]}")

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
            self.rectangle_handler.add_rectangle(current_image, rect, class_id, self.image_info)
    
    def update_rectangle(self, index, rect, class_id=0):
        """Mevcut bir dikdörtgeni günceller"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            self.rectangle_handler.update_rectangle(current_image, index, rect, class_id, self.image_info)
    
    def delete_rectangle(self, index):
        """Seçili dikdörtgeni siler"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            if self.rectangle_handler.delete_rectangle(current_image, index):
                print(f"Dikdörtgen silindi: indeks {index}")
    
    def clear_rectangles(self):
        """Geçerli resmin dikdörtgenlerini temizler"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            self.rectangle_handler.clear_rectangles(current_image)
            self.image_label.clearRectangles()


    def save_annotations(self, format="yolo"):
        """Tüm annotationları txt dosyalarına kaydeder"""
        if not self.image_paths:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek görüntü yok!")
            return

        # Annotation manager üzerinden kaydet
        self.annotation_manager.save_annotations(format)
        
        format_name = "YOLO" if format == "yolo" else "standart"
        QMessageBox.information(
            self,
            "Bilgi",
            f"Annotationlar {self.output_dir} klasörüne {format_name} formatında kaydedildi!",
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "image_paths") and self.image_paths:
            self.display_image()
