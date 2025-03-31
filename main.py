from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
import sys
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("data/icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())