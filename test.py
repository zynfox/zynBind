from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap
import sys

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Test")
        self.setMinimumSize(200, 100)

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)

        # Load and display the image
        pixmap = QPixmap("C:/Users/zork/Projects/Github/zynfox/zynBind/img/switch_off.png")
        if pixmap.isNull():
            print("Failed to load image.")
        else:
            self.label.setPixmap(pixmap)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())