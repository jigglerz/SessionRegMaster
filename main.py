import sys
from PyQt6.QtWidgets import QApplication
from api_app import APIApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    api_app = APIApp()
    api_app.show()
    sys.exit(app.exec())
