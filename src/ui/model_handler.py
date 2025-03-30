import os
from ultralytics import YOLO
import torch
from PyQt6.QtCore import QThread, pyqtSignal
import cv2

class ModelHandler:
    """YOLOv8 modelini yönetir ve resimleri otomatik etiketler"""
    
    def __init__(self, annotation_manager):
        self.annotation_manager = annotation_manager
        self.model = None
        self.model_path = ""
        self.confidence_threshold = 0.5  # Varsayılan eşik değeri
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self, model_path):
        """Bir YOLOv8 modelini yükler"""
        try:
            self.model_path = model_path
            
            # Model yükleniyor
            self.model = YOLO(model_path)
            
            # Sınıf bilgilerini al
            class_names = self.model.names
            
            # Modelin sınıf isimlerini annotation manager'a aktar
            self.annotation_manager.class_names = [class_names[i] for i in range(len(class_names))]
            
            print(f"Model başarıyla yüklendi: {model_path}")
            print(f"Sınıflar: {self.annotation_manager.class_names}")
            
            return True, "Model başarıyla yüklendi"
        except Exception as e:
            print(f"Model yüklenirken hata: {e}")
            return False, f"Model yüklenirken hata: {e}"
    
    def detect_objects(self, image_path):
        """Bir resimde nesneleri tespit eder ve annotation olarak kaydeder"""
        if not self.model:
            return False, "Model yüklenmedi"
        
        try:
            # Resmi oku
            image = cv2.imread(image_path)
            if image is None:
                return False, f"Resim okunamadı: {image_path}"
            
            # YOLOv8 nesne tespiti yap
            results = self.model(image, conf=self.confidence_threshold)
            
            # Sonuçları al
            boxes = results[0].boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2 formatında
            classes = results[0].boxes.cls.cpu().numpy()  # Sınıf indeksleri
            
            # Resim boyutları 
            img_height, img_width = image.shape[:2]
            
            # Önce mevcut annotationları temizle
            self.annotation_manager.clear_rectangles(image_path)
            
            # Her tespit edilen nesne için dikdörtgen ekle
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                
                # Koordinatları integer'a çevir
                x = int(x1)
                y = int(y1)
                w = int(x2 - x1)
                h = int(y2 - y1)
                
                # Sınıf indeksi
                class_id = int(classes[i])
                
                # Dikdörtgeni ekle
                self.annotation_manager.add_rectangle(image_path, x, y, w, h, class_id)
            
            return True, f"{len(boxes)} nesne tespit edildi"
        except Exception as e:
            print(f"Nesne tespiti sırasında hata: {e}")
            return False, f"Nesne tespiti sırasında hata: {e}"
    
    def process_folder(self, folder_path, progress_callback=None):
        """Bir klasördeki tüm resimlerde nesne tespiti yapar"""
        if not self.model:
            return False, "Model yüklenmedi"
        
        # Klasördeki resim dosyalarını bul
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.JPG', '.JPEG', '.PNG']
        image_files = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            return False, "Klasörde resim bulunamadı"
        
        # Her resim için nesne tespiti yap
        total_objects = 0
        for i, image_path in enumerate(image_files):
            success, message = self.detect_objects(image_path)
            if success:
                num_objects = len(self.annotation_manager.get_annotations(image_path))
                total_objects += num_objects
                
                # İlerleme geri çağrısı
                if progress_callback:
                    progress_callback(i+1, len(image_files), image_path, num_objects)
            else:
                print(f"Hata: {message} - {image_path}")
        
        return True, f"İşlem tamamlandı: {len(image_files)} resimde toplam {total_objects} nesne tespit edildi"