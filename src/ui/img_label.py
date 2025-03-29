from PyQt6.QtWidgets import QLabel

from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent, QCursor
from PyQt6.QtCore import Qt, QRect, QPoint


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.rectangles = []  # Dikdörtgenler
        self.rectangle_classes = []  # Dikdörtgenlere karşılık gelen sınıflar
        self.current_rect = None
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.setMouseTracking(True)

        # Dikdörtgen düzenleme için değişkenler
        self.selected_rect_index = -1
        self.dragging = False
        self.resize_mode = False
        self.resize_handle = None
        self.drag_start_point = QPoint()
        self.hover_rect_index = -1

        # Görüntü ölçeklendirme değişkenleri
        self.offset_x = 0
        self.offset_y = 0
        self.orig_width = 0
        self.orig_height = 0
        self.scaled_width = 0
        self.scaled_height = 0

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Mevcut bir dikdörtgenin üzerinde mi kontrol et
            self.selected_rect_index = self.get_rect_at_position(
                event.position().toPoint()
            )

            if self.selected_rect_index >= 0:
                # Mevcut dikdörtgen seçildi
                self.dragging = True
                self.drag_start_point = event.position().toPoint()

                # Seçilen dikdörtgenin sınıfını göster
                if self.selected_rect_index < len(self.rectangle_classes):
                    class_id = self.rectangle_classes[self.selected_rect_index]
                    self.parent.show_selected_class(class_id)

                # Yeniden boyutlandırma köşesi/kenarı seçildi mi kontrol et
                self.resize_handle = self.get_resize_handle(
                    self.rectangles[self.selected_rect_index],
                    event.position().toPoint(),
                )
                if self.resize_handle:
                    self.resize_mode = True
                    self.dragging = False
            else:
                # Yeni dikdörtgen çizimi başlatılıyor
                self.drawing = True
                self.start_point = event.position().toPoint()
                self.end_point = self.start_point
                self.current_rect = QRect(self.start_point, self.end_point)

            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()

        # Hangi dikdörtgenin üzerindeyiz?
        self.hover_rect_index = self.get_rect_at_position(pos)

        # Fare imlecini güncelle
        if self.hover_rect_index >= 0:
            resize_handle = self.get_resize_handle(
                self.rectangles[self.hover_rect_index], pos
            )
            if resize_handle:
                # Yeniden boyutlandırma imleçleri
                if resize_handle in ["top-left", "bottom-right"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
                elif resize_handle in ["top-right", "bottom-left"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
                elif resize_handle in ["top", "bottom"]:
                    self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
                else:  # left, right
                    self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            else:
                # Taşıma imleci
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        else:
            # Standart imleç
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        if self.drawing:
            # Yeni dikdörtgen çiziliyor
            self.end_point = pos
            self.current_rect = QRect(self.start_point, self.end_point)
            self.update()
        elif self.dragging and self.selected_rect_index >= 0:
            # Dikdörtgen taşınıyor
            delta = pos - self.drag_start_point
            rect = self.rectangles[self.selected_rect_index]
            self.rectangles[self.selected_rect_index] = rect.translated(delta)
            self.drag_start_point = pos
            self.update()
        elif self.resize_mode and self.selected_rect_index >= 0:
            # Dikdörtgen yeniden boyutlandırılıyor
            rect = self.rectangles[self.selected_rect_index]
            new_rect = self.resize_rectangle(rect, pos, self.resize_handle)
            if new_rect.width() > 5 and new_rect.height() > 5:
                self.rectangles[self.selected_rect_index] = new_rect
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing:
                # Yeni dikdörtgen oluşturma tamamlandı
                self.drawing = False
                self.end_point = event.position().toPoint()

                # Minimum boyut kontrolü
                rect = QRect(self.start_point, self.end_point).normalized()
                if rect.width() > 5 and rect.height() > 5:
                    # Seçilen sınıfı al
                    class_id = self.parent.get_selected_class_id()

                    # Dikdörtgeni ve sınıfını ekle
                    self.rectangles.append(rect)
                    self.rectangle_classes.append(class_id)

                    # Ana pencereye bildir
                    self.parent.add_rectangle_to_current_image(rect, class_id)

                self.current_rect = None
            elif self.dragging and self.selected_rect_index >= 0:
                # Taşıma işlemi tamamlandı
                self.dragging = False
                # Taşınan dikdörtgeni güncelle
                rect = self.rectangles[self.selected_rect_index]
                class_id = self.rectangle_classes[self.selected_rect_index]
                self.parent.update_rectangle(self.selected_rect_index, rect, class_id)
            elif self.resize_mode and self.selected_rect_index >= 0:
                # Yeniden boyutlandırma tamamlandı
                self.resize_mode = False
                # Yeniden boyutlandırılan dikdörtgeni güncelle
                rect = self.rectangles[self.selected_rect_index]
                class_id = self.rectangle_classes[self.selected_rect_index]
                self.parent.update_rectangle(self.selected_rect_index, rect, class_id)
                self.resize_handle = None

            self.update()

    def set_rect_class(self, class_id):
        """Seçili dikdörtgenin sınıfını değiştirir"""
        if self.selected_rect_index >= 0 and self.selected_rect_index < len(
            self.rectangle_classes
        ):
            self.rectangle_classes[self.selected_rect_index] = class_id
            rect = self.rectangles[self.selected_rect_index]
            self.parent.update_rectangle(self.selected_rect_index, rect, class_id)
            self.update()

    def get_rect_at_position(self, pos):
        """Verilen pozisyonda bir dikdörtgen varsa indeksini döndürür, yoksa -1"""
        for i in range(
            len(self.rectangles) - 1, -1, -1
        ):  # Sondan başa doğru kontrol et (üstteki dikdörtgenler öncelikli)
            if self.rectangles[i].contains(pos):
                return i
        return -1

    def get_resize_handle(self, rect, pos, handle_size=10):
        """Pozisyonun dikdörtgenin hangi yeniden boyutlandırma tutamaçında olduğunu döndürür"""
        # Köşe tutamaçları
        if QRect(
            int(rect.topLeft().x() - handle_size / 2),
            int(rect.topLeft().y() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "top-left"
        if QRect(
            int(rect.topRight().x() - handle_size / 2),
            int(rect.topRight().y() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "top-right"
        if QRect(
            int(rect.bottomLeft().x() - handle_size / 2),
            int(rect.bottomLeft().y() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "bottom-left"
        if QRect(
            int(rect.bottomRight().x() - handle_size / 2),
            int(rect.bottomRight().y() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "bottom-right"

        # Kenar tutamaçları
        if QRect(
            int(rect.left() - handle_size / 2),
            int(rect.top() + rect.height() / 2 - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "left"
        if QRect(
            int(rect.right() - handle_size / 2),
            int(rect.top() + rect.height() / 2 - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "right"
        if QRect(
            int(rect.left() + rect.width() / 2 - handle_size / 2),
            int(rect.top() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "top"
        if QRect(
            int(rect.left() + rect.width() / 2 - handle_size / 2),
            int(rect.bottom() - handle_size / 2),
            handle_size,
            handle_size,
        ).contains(pos):
            return "bottom"

        return None

    def resize_rectangle(self, rect, pos, handle):
        """Dikdörtgeni tutamaç ve yeni pozisyona göre yeniden boyutlandırır"""
        new_rect = QRect(rect)

        if handle == "top-left":
            new_rect.setTopLeft(pos)
        elif handle == "top-right":
            new_rect.setTopRight(pos)
        elif handle == "bottom-left":
            new_rect.setBottomLeft(pos)
        elif handle == "bottom-right":
            new_rect.setBottomRight(pos)
        elif handle == "left":
            new_rect.setLeft(pos.x())
        elif handle == "right":
            new_rect.setRight(pos.x())
        elif handle == "top":
            new_rect.setTop(pos.y())
        elif handle == "bottom":
            new_rect.setBottom(pos.y())

        return (
            new_rect.normalized()
        )  # Normalize et (genişlik/yükseklik negatif olmasın)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap():
            return

        painter = QPainter(self)

        # Tüm kaydedilmiş dikdörtgenleri çiz
        for i, rect in enumerate(self.rectangles):
            # Dikdörtgenin sınıfına göre renk belirleyelim
            class_id = (
                self.rectangle_classes[i] if i < len(self.rectangle_classes) else 0
            )

            # Sınıf renklerini tanımlayalım (sınıf sayısına göre artırılabilir)
            class_colors = [
                QColor(255, 0, 0),  # Kırmızı (default)
                QColor(0, 255, 0),  # Yeşil
                QColor(0, 0, 255),  # Mavi
                QColor(255, 255, 0),  # Sarı
                QColor(255, 0, 255),  # Magenta
                QColor(0, 255, 255),  # Cyan
                QColor(255, 165, 0),  # Turuncu
                QColor(128, 0, 128),  # Mor
                QColor(165, 42, 42),  # Kahverengi
                QColor(0, 128, 0),  # Koyu yeşil
            ]

            # Sınıf rengi
            class_color = class_colors[class_id % len(class_colors)]

            if i == self.selected_rect_index:
                # Seçili dikdörtgen daha kalın çizilir
                painter.setPen(QPen(class_color, 3))
            elif i == self.hover_rect_index:
                # Fare üzerinde durulan dikdörtgen noktalı çizilir
                pen = QPen(class_color, 2)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
            else:
                painter.setPen(QPen(class_color, 2))

            painter.drawRect(rect)

            # Sınıf etiketini göster
            class_name = self.parent.get_class_name(class_id)
            painter.drawText(rect.topLeft() + QPoint(5, -5), class_name)

            # Seçili dikdörtgenin tutamaçlarını çiz
            if i == self.selected_rect_index:
                handle_size = 8
                # Tutamaçlar dikdörtgenin rengini kullanır
                # 8 tutamaç (köşeler ve kenarlar)
                painter.fillRect(
                    int(rect.topLeft().x() - handle_size / 2),
                    int(rect.topLeft().y() - handle_size / 2),
                    handle_size,
                    handle_size,
                    class_color,
                )
                # Diğer tutamaçlar...

        # Çizim sırasındaki dikdörtgeni çiz
        if self.drawing and self.current_rect:
            # Çizim sırasında seçilen sınıfın rengini kullan
            class_id = self.parent.get_selected_class_id()
            class_colors = [
                QColor(255, 0, 0),
                QColor(0, 255, 0),
                QColor(0, 0, 255),
                QColor(255, 255, 0),
                QColor(255, 0, 255),
                QColor(0, 255, 255),
            ]
            painter.setPen(QPen(class_colors[class_id % len(class_colors)], 2))
            painter.drawRect(self.current_rect)

    def clearRectangles(self):
        self.rectangles = []
        self.rectangle_classes = []
        self.selected_rect_index = -1
        self.hover_rect_index = -1
        self.update()

    def keyPressEvent(self, event):
        # Delete tuşu ile seçili dikdörtgeni sil
        if event.key() == Qt.Key.Key_Delete and self.selected_rect_index >= 0:
            self.parent.delete_rectangle(self.selected_rect_index)
            self.rectangles.pop(self.selected_rect_index)
            self.rectangle_classes.pop(self.selected_rect_index)
            self.selected_rect_index = -1
            self.update()
        else:
            super().keyPressEvent(event)
