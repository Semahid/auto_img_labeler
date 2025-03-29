from PyQt6.QtCore import QRect

class RectangleHandler:
    """Dikdörtgenlerle ilgili koordinat dönüşümlerini ve diğer işlemleri yönetir"""
    
    def __init__(self, annotation_manager):
        self.annotation_manager = annotation_manager
    
    def display_to_original(self, rect, image_info):
        """Gösterilen koordinatları orijinal resim koordinatlarına dönüştürür"""
        # QLabel içindeki offseti çıkar
        display_x = rect.x() - image_info.offset_x
        display_y = rect.y() - image_info.offset_y
        display_w = rect.width()
        display_h = rect.height()

        # Ölçekleme oranları
        scale_x = image_info.orig_width / image_info.scaled_width
        scale_y = image_info.orig_height / image_info.scaled_height

        # Gösterilen koordinatları orijinal resim koordinatlarına çevir
        orig_x = int(display_x * scale_x)
        orig_y = int(display_y * scale_y)
        orig_w = int(display_w * scale_x)
        orig_h = int(display_h * scale_y)

        # Sınırları kontrol et
        orig_x = max(0, min(orig_x, image_info.orig_width - 1))
        orig_y = max(0, min(orig_y, image_info.orig_height - 1))
        orig_w = min(orig_w, image_info.orig_width - orig_x)
        orig_h = min(orig_h, image_info.orig_height - orig_y)
        
        return orig_x, orig_y, orig_w, orig_h
    
    def original_to_display(self, orig_x, orig_y, orig_w, orig_h, image_info):
        """Orijinal resim koordinatlarını gösterilen koordinatlara dönüştürür"""
        # Ölçekleme oranları
        scale_x = image_info.scaled_width / image_info.orig_width
        scale_y = image_info.scaled_height / image_info.orig_height
        
        # Dönüştür ve offset ekle
        display_x = int(orig_x * scale_x) + image_info.offset_x
        display_y = int(orig_y * scale_y) + image_info.offset_y
        display_w = int(orig_w * scale_x)
        display_h = int(orig_h * scale_y)
        
        return QRect(display_x, display_y, display_w, display_h)
    
    def add_rectangle(self, img_path, rect, class_id, image_info):
        """Bir resme yeni dikdörtgen ekler"""
        orig_x, orig_y, orig_w, orig_h = self.display_to_original(rect, image_info)
        
        # Kaydedilecek koordinatlar
        result = self.annotation_manager.add_rectangle(
            img_path, orig_x, orig_y, orig_w, orig_h, class_id
        )
        
        # Debug bilgisi
        print(f"Dikdörtgen eklendi (orijinal): x={orig_x}, y={orig_y}, w={orig_w}, h={orig_h}, class_id={class_id}")
        print(f"Ölçekleme faktörleri: {image_info.orig_width/image_info.scaled_width:.3f}x, "
              f"{image_info.orig_height/image_info.scaled_height:.3f}y, "
              f"Offset: {image_info.offset_x}, {image_info.offset_y}")
        
        return result
    
    def update_rectangle(self, img_path, index, rect, class_id, image_info):
        """Mevcut bir dikdörtgeni günceller"""
        # Önce annotations kontrolü
        annotations = self.annotation_manager.get_annotations(img_path)
        if 0 <= index < len(annotations):
            orig_x, orig_y, orig_w, orig_h = self.display_to_original(rect, image_info)
            
            # Güncelle
            result = self.annotation_manager.update_rectangle(
                img_path, index, orig_x, orig_y, orig_w, orig_h, class_id
            )
            
            # Debug bilgisi
            print(f"Dikdörtgen güncellendi (orijinal): x={orig_x}, y={orig_y}, w={orig_w}, h={orig_h}, class_id={class_id}")
            print(f"Ölçekleme faktörleri: {image_info.orig_width/image_info.scaled_width:.3f}x, "
                  f"{image_info.orig_height/image_info.scaled_height:.3f}y, "
                  f"Offset: {image_info.offset_x}, {image_info.offset_y}")
            
            return result
        return False
    
    def delete_rectangle(self, img_path, index):
        """Bir dikdörtgeni siler"""
        return self.annotation_manager.delete_rectangle(img_path, index)
    
    def clear_rectangles(self, img_path):
        """Bir resmin tüm dikdörtgenlerini temizler"""
        return self.annotation_manager.clear_rectangles(img_path)
    
    def get_rectangles_for_display(self, img_path, image_info):
        """Orijinal dikdörtgenleri, gösterim için uygun formata dönüştürür"""
        annotations = self.annotation_manager.get_annotations(img_path)
        display_rects = []
        class_ids = []
        
        for annotation in annotations:
            if len(annotation) == 5:  # x, y, w, h, class_id
                orig_x, orig_y, orig_w, orig_h, class_id = annotation
            else:  # Eski format, sınıfsız
                orig_x, orig_y, orig_w, orig_h = annotation
                class_id = 0  # Varsayılan sınıf
            
            # Orijinal koordinatları görüntü koordinatlarına dönüştür
            rect = self.original_to_display(orig_x, orig_y, orig_w, orig_h, image_info)
            
            display_rects.append(rect)
            class_ids.append(class_id)
        
        return display_rects, class_ids



class ImageInfo:
    """Görüntülenen resmin boyut ve pozisyon bilgilerini içerir"""
    
    def __init__(self):
        self.orig_width = 0    # Orijinal genişlik
        self.orig_height = 0   # Orijinal yükseklik
        self.scaled_width = 0  # Ölçeklenmiş genişlik
        self.scaled_height = 0 # Ölçeklenmiş yükseklik
        self.offset_x = 0      # X eksenindeki offset
        self.offset_y = 0      # Y eksenindeki offset
    
    def update(self, orig_width, orig_height, scaled_width, scaled_height, offset_x, offset_y):
        """Tüm değerleri bir defada günceller"""
        self.orig_width = orig_width
        self.orig_height = orig_height
        self.scaled_width = scaled_width
        self.scaled_height = scaled_height
        self.offset_x = offset_x
        self.offset_y = offset_y