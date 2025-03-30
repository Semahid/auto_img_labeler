import glob
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QLineEdit,
    QApplication,
    QGridLayout,
)

from src.ui.img_label import ImageLabel
from src.ui.rectangle_handler import ImageInfo, RectangleHandler
from src.utils.model_handler import ModelHandler
from src.utils.annotation_manager import AnnotationManager
from src.utils.dataset_splitter import DatasetSplitter


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

        # Model Yönetimi için bileşenler
        self.model_group = QGroupBox("Model Yönetimi")
        self.model_layout = QVBoxLayout()

        # Model dosyası seçme
        self.model_path_layout = QHBoxLayout()
        self.model_path_label = QLabel("Model:")
        self.model_path_input = QLineEdit()
        self.model_path_input.setReadOnly(True)
        self.model_browse_button = QPushButton("Gözat")
        self.model_browse_button.clicked.connect(self.browse_model)

        self.model_path_layout.addWidget(self.model_path_label)
        self.model_path_layout.addWidget(self.model_path_input)
        self.model_path_layout.addWidget(self.model_browse_button)

        # Güven eşiği
        self.confidence_layout = QHBoxLayout()
        self.confidence_label = QLabel("Güven Eşiği:")
        self.confidence_input = QLineEdit("0.5")
        self.confidence_layout.addWidget(self.confidence_label)
        self.confidence_layout.addWidget(self.confidence_input)

        # Model işlemleri butonları
        self.auto_label_button = QPushButton("Otomatik Etiketle")
        self.auto_label_button.clicked.connect(self.auto_label_current_image)

        self.process_all_simple_button = QPushButton("Basit Toplu İşlem")
        self.process_all_simple_button.clicked.connect(self.process_all_images_simple)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_status = QLabel("")
        self.progress_status.setVisible(False)

        # Düzene ekle
        self.model_layout.addLayout(self.model_path_layout)
        self.model_layout.addLayout(self.confidence_layout)
        self.model_layout.addWidget(self.auto_label_button)
        self.model_layout.addWidget(self.process_all_simple_button)
        self.model_layout.addWidget(self.progress_bar)
        self.model_layout.addWidget(self.progress_status)

        self.model_group.setLayout(self.model_layout)

        self.ui_data_parser()

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
        button_layout.addWidget(self.model_group)
        button_layout.addWidget(self.dataset_group)

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

        # Model işleyici
        self.model_handler = ModelHandler(self.annotation_manager)

        # Batch işleme worker
        self.batch_worker = None

        # Resim bilgisi nesnesi
        self.image_info = ImageInfo()

        self.update_class_combo()
        # Yeni metod ekleyin

    def ui_data_parser(self):
        # MainWindow.__init__ metoduna ekleyin:
        # Dataset bölümlendirme grubu
        self.dataset_group = QGroupBox("Veri Seti Yönetimi")
        self.dataset_layout = QVBoxLayout()

        # Bölümlendirme oranları
        self.split_layout = QGridLayout()

        # Train set
        self.train_label = QLabel("Train:")
        self.train_input = QLineEdit("70")
        self.train_input.setToolTip("Eğitim seti yüzde oranı (0-100)")
        self.split_layout.addWidget(self.train_label, 0, 0)
        self.split_layout.addWidget(self.train_input, 0, 1)

        # Validation set
        self.val_label = QLabel("Validation:")
        self.val_input = QLineEdit("20")
        self.val_input.setToolTip("Doğrulama seti yüzde oranı (0-100)")
        self.split_layout.addWidget(self.val_label, 1, 0)
        self.split_layout.addWidget(self.val_input, 1, 1)

        # Test set
        self.test_label = QLabel("Test:")
        self.test_input = QLineEdit("10")
        self.test_input.setToolTip("Test seti yüzde oranı (0-100)")
        self.split_layout.addWidget(self.test_label, 2, 0)
        self.split_layout.addWidget(self.test_input, 2, 1)

        # Toplam kontrol
        self.total_ratio_label = QLabel("Toplam: 100%")
        self.split_layout.addWidget(self.total_ratio_label, 3, 0, 1, 2)

        # Oranları kontrol etmek için event bağlantıları
        self.train_input.textChanged.connect(self.check_split_ratios)
        self.val_input.textChanged.connect(self.check_split_ratios)
        self.test_input.textChanged.connect(self.check_split_ratios)

        # Veri seti bölümlendirme butonları
        self.split_data_button = QPushButton("Veri Setini Böl")
        self.split_data_button.clicked.connect(self.split_dataset)

        # Layout'a ekle
        self.dataset_layout.addLayout(self.split_layout)
        self.dataset_layout.addWidget(self.split_data_button)

        self.dataset_group.setLayout(self.dataset_layout)

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
        for class_name in self.annotation_manager.class_names:
            self.class_combo.addItem(class_name)

    def get_selected_class_id(self):
        """Şu anda seçili olan sınıfın ID'sini döndürür"""
        return self.class_combo.currentIndex()

    def get_class_name(self, class_id):
        """Sınıf ID'sine göre sınıf adını döndürür"""
        if 0 <= class_id < len(self.annotation_manager.class_names):
            return self.annotation_manager.class_names[class_id]
        return "unknown"

    def show_selected_class(self, class_id):
        """Verilen sınıfı combo box'ta seçer"""
        if 0 <= class_id < len(self.annotation_manager.class_names):
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
            self.update_class_combo()
            # Yeni eklenen sınıfı seç
            self.class_combo.setCurrentIndex(
                len(self.annotation_manager.class_names) - 1
            )

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
            display_rects, class_ids = (
                self.rectangle_handler.get_rectangles_for_display(
                    current_image, self.image_info
                )
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
            self.rectangle_handler.add_rectangle(
                current_image, rect, class_id, self.image_info
            )

    def update_rectangle(self, index, rect, class_id=0):
        """Mevcut bir dikdörtgeni günceller"""
        if self.image_paths and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            self.rectangle_handler.update_rectangle(
                current_image, index, rect, class_id, self.image_info
            )

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

    def browse_model(self):
        """YOLOv8 model dosyasını seçin"""
        model_path, _ = QFileDialog.getOpenFileName(
            self,
            "YOLOv8 Modelini Seç",
            "",
            "Model Dosyaları (*.pt *.pth);;Tüm Dosyalar (*)",
        )
        if model_path:
            self.model_path_input.setText(model_path)
            # Güven eşiğini ayarla
            try:
                confidence = float(self.confidence_input.text())
                self.model_handler.confidence_threshold = min(
                    max(0.05, confidence), 1.0
                )
            except ValueError:
                self.model_handler.confidence_threshold = 0.5
                self.confidence_input.setText("0.5")

            # Modeli yükle
            success, message = self.model_handler.load_model(model_path)
            if success:
                QMessageBox.information(self, "Bilgi", message)
                self.update_class_combo()
            else:
                QMessageBox.warning(self, "Uyarı", message)

    def auto_label_current_image(self):
        """Mevcut resmi otomatik etiketle"""
        if not self.model_handler.model:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir model yükleyin.")
            return

        if not self.image_paths or self.current_index >= len(self.image_paths):
            QMessageBox.warning(self, "Uyarı", "Etiketlenecek bir resim yok.")
            return

        current_image = self.image_paths[self.current_index]

        # Güven eşiğini güncelle
        try:
            confidence = float(self.confidence_input.text())
            self.model_handler.confidence_threshold = min(max(0.05, confidence), 1.0)
        except ValueError:
            self.model_handler.confidence_threshold = 0.5
            self.confidence_input.setText("0.5")

        # Mevcut dikdörtgenleri temizle
        self.clear_rectangles()

        # Nesne tespiti yap
        success, message = self.model_handler.detect_objects(current_image)

        if success:
            # Görüntüyü güncelle
            self.display_image()
            QMessageBox.information(self, "Bilgi", message)
        else:
            QMessageBox.warning(self, "Uyarı", message)

    def process_all_images_simple(self):
        """Tüm resimleri basit bir şekilde otomatik etiketle"""
        if not self.model_handler.model:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir model yükleyin.")
            return

        if not self.image_paths:
            QMessageBox.warning(self, "Uyarı", "Açık bir klasör yok.")
            return

        reply = QMessageBox.question(
            self,
            "Toplu İşlem",
            f"Tüm resimler ({len(self.image_paths)}) otomatik etiketlenecek. Devam etmek istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # İlerleme çubuğunu göster
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_status.setText("İşlem başlıyor...")
        self.progress_status.setVisible(True)

        # Butonları devre dışı bırak
        self.auto_label_button.setEnabled(False)
        self.model_browse_button.setEnabled(False)

        # Başlangıç indeksini kaydet
        original_index = self.current_index

        # Her resim için işlem yap
        total_objects = 0
        try:
            for i, image_path in enumerate(self.image_paths):
                # İlerlemeyi güncelle
                percent = int(((i + 1) / len(self.image_paths)) * 100)
                self.progress_bar.setValue(percent)
                self.progress_status.setText(
                    f"İşleniyor: {i+1}/{len(self.image_paths)} - {os.path.basename(image_path)}"
                )

                # Geçerli görüntüyü ayarla
                self.current_index = i

                # Mevcut dikdörtgenleri temizle
                self.clear_rectangles()

                # Nesne tespiti yap
                success, message = self.model_handler.detect_objects(image_path)

                if success:
                    # Bulunan nesnelerin sayısını al
                    objects_count = len(
                        self.annotation_manager.get_annotations(image_path)
                    )
                    total_objects += objects_count

                    # İlerleme mesajını güncelle
                    self.progress_status.setText(
                        f"İşleniyor: {i+1}/{len(self.image_paths)} - {os.path.basename(image_path)} - {objects_count} nesne bulundu"
                    )

                # QApplication'ın olayları işlemesine izin ver
                QApplication.processEvents()

            # İşlem tamamlandı
            QMessageBox.information(
                self,
                "Bilgi",
                f"İşlem tamamlandı: {len(self.image_paths)} resimde toplam {total_objects} nesne tespit edildi",
            )
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İşlem sırasında hata oluştu: {e}")
        finally:
            # İlerleme çubuğunu kapat
            self.progress_bar.setVisible(False)
            self.progress_status.setVisible(False)

            # Butonları etkinleştir
            self.auto_label_button.setEnabled(True)
            self.model_browse_button.setEnabled(True)

            # Orijinal görüntüye dön
            self.current_index = original_index
            self.display_image()

            # Sonuçları kaydet
            self.save_annotations(self.output_format)

    def check_split_ratios(self):
        """Train, validation ve test setlerinin oranlarını kontrol eder"""
        try:
            train_ratio = int(self.train_input.text())
            val_ratio = int(self.val_input.text())
            test_ratio = int(self.test_input.text())

            total = train_ratio + val_ratio + test_ratio

            # Renkleri güncelle
            if total == 100:
                self.total_ratio_label.setText(f"Toplam: {total}% ✓")
                self.total_ratio_label.setStyleSheet("color: green;")
                self.split_data_button.setEnabled(True)
            else:
                self.total_ratio_label.setText(f"Toplam: {total}% ✗")
                self.total_ratio_label.setStyleSheet("color: red;")
                self.split_data_button.setEnabled(False)
        except ValueError:
            self.total_ratio_label.setText("Geçersiz değer!")
            self.total_ratio_label.setStyleSheet("color: red;")
            self.split_data_button.setEnabled(False)

    def split_dataset(self):
        """Veri setini train, validation ve test olarak böler"""
        if not self.image_paths:
            QMessageBox.warning(self, "Uyarı", "Açık bir klasör yok.")
            return

        try:
            # Oranları al
            train_ratio = int(self.train_input.text())
            val_ratio = int(self.val_input.text())
            test_ratio = int(self.test_input.text())

            # Toplam kontrolü
            if train_ratio + val_ratio + test_ratio != 100:
                QMessageBox.warning(self, "Uyarı", "Oranların toplamı 100 olmalıdır!")
                return

            # Kaynak klasörü al
            source_dir = os.path.dirname(self.image_paths[0])

            # Hedef klasörü sor
            output_dir = QFileDialog.getExistingDirectory(
                self, "Veri Seti Çıktı Klasörünü Seçin", source_dir
            )

            if not output_dir:
                return

            # İlerleme çubuğunu göster
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.progress_status.setText("Veri seti bölümlendiriliyor...")
            self.progress_status.setVisible(True)

            # Butonları devre dışı bırak
            self.split_data_button.setEnabled(False)

            # Event loop'unun işlenmesi için güncelle
            QApplication.processEvents()

            # Splitter'ı oluştur ve bölümlendir
            splitter = DatasetSplitter(source_dir, output_dir)
            result = splitter.split_dataset(train_ratio, val_ratio, test_ratio)

            # İlerleme çubuğunu güncelle
            self.progress_bar.setValue(100)
            self.progress_status.setText("Veri seti bölümlendirme tamamlandı!")

            # Sonuçları göster
            message = (
                f"Veri seti başarıyla bölümlendi:\n\n"
                f"Train: {result['train_count']} resim ({train_ratio}%)\n"
                f"Validation: {result['val_count']} resim ({val_ratio}%)\n"
                f"Test: {result['test_count']} resim ({test_ratio}%)\n\n"
                f"Toplam: {result['total_count']} resim\n\n"
                f"Veri seti klasörü: {result['dataset_dir']}\n"
                f"data.yaml: {result['yaml_path']}"
            )

            QMessageBox.information(self, "Veri Seti Bölümlendirme", message)

        except Exception as e:
            QMessageBox.warning(
                self, "Hata", f"Veri seti bölümlendirme sırasında hata: {str(e)}"
            )
        finally:
            # İlerleme çubuğunu kapat
            self.progress_bar.setVisible(False)
            self.progress_status.setVisible(False)

            # Butonları etkinleştir
            self.split_data_button.setEnabled(True)
