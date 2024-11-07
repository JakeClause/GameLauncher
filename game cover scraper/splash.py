import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setPixmap(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Load and display splash screen
    splash_pix = QPixmap('icon (png).png')
    splash = SplashScreen(splash_pix)
    splash.show()
    
    # Close splash screen after 10 seconds
    QTimer.singleShot(5000, splash.close)
    
    sys.exit(app.exec_())
