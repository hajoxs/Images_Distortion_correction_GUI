
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("畸变矫正")
        self.setGeometry(100, 100, 400, 300)

        self.initUI()

    def initUI(self):
        self.image_correction_button = QPushButton('图像畸变矫正', self)
        self.image_correction_button.setGeometry(50, 50, 300, 50)
        self.image_correction_button.clicked.connect(self.image_correction_clicked)

        self.video_correction_button = QPushButton('视频畸变矫正', self)
        self.video_correction_button.setGeometry(50, 150, 300, 50)
        self.video_correction_button.clicked.connect(self.video_correction_clicked)

        self.exit_button = QPushButton('退出', self)
        self.exit_button.setGeometry(50, 250, 300, 50)
        self.exit_button.clicked.connect(self.exit_clicked)

    def image_correction_clicked(self):
        # Open the image correction interface
        from image_correction import ImageUndistortionGUI
        self.image_correction_ui = ImageUndistortionGUI()
        self.image_correction_ui.show()

    def video_correction_clicked(self):
        # Open the video correction interface
        from video_correction import VideoDistortionCorrectionGUI
        self.video_correction_ui = VideoDistortionCorrectionGUI()
        self.video_correction_ui.show()

    def exit_clicked(self):
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ui = MainUI()
    main_ui.show()
    sys.exit(app.exec_())
