import os
import json
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox


class AnnotationManager:
    def __init__(self):
        self.annotations = {}  # Dictionary to store annotations for each image
        self.output_dir = ""  # Directory to save annotations
        self.class_names = ["default"]  # Default class
        self.classes_file = ""  # File to store class information

    def initialize(self, image_paths, output_dir):
        """Initialize annotations for a set of images"""
        self.output_dir = output_dir
        self.classes_file = os.path.join(self.output_dir, "classes.json")

        # Initialize empty annotations for each image
        self.annotations = {}
        for img_path in image_paths:
            self.annotations[img_path] = []

        # Load existing class information
        self.load_classes()

        # Load existing annotations
        self.load_existing_annotations(image_paths)

    def load_classes(self):
        """Load class information from file"""
        if os.path.exists(self.classes_file):
            try:
                with open(self.classes_file, "r") as f:
                    self.class_names = json.load(f)
                    if not self.class_names:  # Check for empty list
                        self.class_names = ["default"]
                    print(f"Classes loaded: {self.class_names}")
            except Exception as e:
                print(f"Error loading classes: {e}")
                self.class_names = ["default"]
        else:
            # Use default classes
            self.class_names = ["default"]

    def save_classes(self):
        """Save class information to file"""
        try:
            with open(self.classes_file, "w") as f:
                json.dump(self.class_names, f)
                print(f"Classes saved: {self.class_names}")
        except Exception as e:
            print(f"Error saving classes: {e}")

    def load_existing_annotations(self, image_paths):
        """Load existing annotations from files"""
        for img_path in image_paths:
            # Create txt filename from image filename
            img_name = os.path.basename(img_path)
            img_name_without_ext = os.path.splitext(img_name)[0]
            txt_path = os.path.join(self.output_dir, f"{img_name_without_ext}.txt")

            if os.path.exists(txt_path):
                # Get image dimensions (needed for YOLO format conversion)
                pixmap = QPixmap(img_path)
                img_width = pixmap.width()
                img_height = pixmap.height()

                with open(txt_path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            parts = line.strip().split()

                            if len(parts) == 5:
                                # Could be YOLO or standard format
                                if (
                                    0 < float(parts[1]) < 1
                                    and 0 < float(parts[2]) < 1
                                    and 0 < float(parts[3]) < 1
                                    and 0 < float(parts[4]) < 1
                                ):
                                    # YOLO format: class_id, x_center_norm, y_center_norm, w_norm, h_norm
                                    class_id = int(parts[0])
                                    x_center_norm = float(parts[1])
                                    y_center_norm = float(parts[2])
                                    w_norm = float(parts[3])
                                    h_norm = float(parts[4])

                                    # Convert normalized coordinates to pixel values
                                    x_center = x_center_norm * img_width
                                    y_center = y_center_norm * img_height
                                    w = w_norm * img_width
                                    h = h_norm * img_height

                                    # Calculate top-left corner coordinates
                                    x = int(x_center - w / 2)
                                    y = int(y_center - h / 2)
                                    w, h = int(w), int(h)

                                    self.annotations[img_path].append(
                                        (x, y, w, h, class_id)
                                    )
                                else:
                                    # Standard format: x, y, w, h, class_id
                                    x, y, w, h, class_id = map(int, parts)
                                    self.annotations[img_path].append(
                                        (x, y, w, h, class_id)
                                    )
                            elif len(parts) == 4:  # x y w h (old format, no class)
                                x, y, w, h = map(int, parts)
                                class_id = 0  # Default class
                                self.annotations[img_path].append(
                                    (x, y, w, h, class_id)
                                )
                            else:
                                print(f"Invalid line format: {line}")
                                continue
                        except Exception as e:
                            print(f"Error parsing line: {line}, {e}")

    def add_rectangle(self, img_path, x, y, w, h, class_id=0):
        """Add a new rectangle annotation"""
        if img_path in self.annotations:
            self.annotations[img_path].append((x, y, w, h, class_id))
            return True
        return False

    def update_rectangle(self, img_path, index, x, y, w, h, class_id):
        """Update an existing rectangle annotation"""
        if img_path in self.annotations and 0 <= index < len(
            self.annotations[img_path]
        ):
            self.annotations[img_path][index] = (x, y, w, h, class_id)
            return True
        return False

    def delete_rectangle(self, img_path, index):
        """Delete a rectangle annotation"""
        if img_path in self.annotations and 0 <= index < len(
            self.annotations[img_path]
        ):
            self.annotations[img_path].pop(index)
            return True
        return False

    def clear_rectangles(self, img_path):
        """Clear all rectangle annotations for an image"""
        if img_path in self.annotations:
            self.annotations[img_path] = []
            return True
        return False

    def get_annotations(self, img_path):
        """Get all annotations for an image"""
        if img_path in self.annotations:
            return self.annotations[img_path]
        return []

    def save_annotations(self, format="yolo"):
        """Tüm annotationları txt dosyalarına kaydeder"""
        # Eğer herhangi bir annotation yoksa işlem yapma
        if not self.annotations:
            print("Kaydedilecek annotation yok!")
            return
        
        # Önce sınıfları kaydet
        self.save_classes()
        
        # Annotations sayacı
        saved_count = 0
        
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
                            # YOLO format: <class_id> <x_center> <y_center> <width> <height> (normalize edilmiş)
                            # Piksel koordinatları hesapla
                            x_center = x + w / 2
                            y_center = y + h / 2
                            
                            # Normalize - koordinatların resim sınırlarını aşmadığını kontrol et
                            x_center = min(max(0, x_center), img_width)
                            y_center = min(max(0, y_center), img_height)
                            
                            x_center_norm = x_center / img_width
                            y_center_norm = y_center / img_height
                            w_norm = w / img_width
                            h_norm = h / img_height
                            
                            # Debug yazdırma
                            print(f"Orijinal: x={x}, y={y}, w={w}, h={h}")
                            print(f"Merkez: x_center={x_center}, y_center={y_center}")
                            print(f"Normalize: x_norm={x_center_norm}, y_norm={y_center_norm}, w_norm={w_norm}, h_norm={h_norm}")
                            
                            f.write(f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")
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
                            
                            # Normalize
                            x_center = min(max(0, x_center), img_width)
                            y_center = min(max(0, y_center), img_height)
                            
                            x_center_norm = x_center / img_width
                            y_center_norm = y_center / img_height
                            w_norm = w / img_width
                            h_norm = h / img_height
                            
                            f.write(f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")
                        else:
                            f.write(f"{x} {y} {w} {h} {class_id}\n")
                
                saved_count += 1
        
        format_name = "YOLO" if format == "yolo" else "standart"
        print(f"{saved_count} resim için annotationlar {self.output_dir} klasörüne {format_name} formatında kaydedildi.")
        return True
