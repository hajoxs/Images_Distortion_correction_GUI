import os
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QLineEdit, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

class ImageProcessor(QThread):
    progress_update = pyqtSignal(int)

    def __init__(self, folder_path, save_folder_path, dist_coeffs, camera_matrix):
        super().__init__()
        self.folder_path = folder_path
        self.save_folder_path = save_folder_path
        self.dist_coeffs = dist_coeffs
        self.camera_matrix = camera_matrix

    def run(self):
        image_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png', '.gif', '.tiff'))]
        total_images = len(image_files)

        for i, file_name in enumerate(image_files):
            image_path = os.path.join(self.folder_path, file_name)
            img = cv2.imread(image_path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)

            if img is not None:
                img_distort = cv2.undistort(img, self.camera_matrix, self.dist_coeffs)
                output_path = os.path.join(self.save_folder_path, 'undistorted_' + file_name)
                cv2.imwrite(output_path, img_distort)

            progress = int((i + 1) * 100 / total_images)
            self.progress_update.emit(progress)

class ImageUndistortionGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("图像畸变矫正")
        self.setGeometry(100, 100, 400, 450)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.select_folder_button = QPushButton("选择文件夹")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.select_folder_button)

        self.folder_path_label = QLabel("选择的文件夹路径：")
        self.layout.addWidget(self.folder_path_label)

        self.select_save_folder_button = QPushButton("选择保存文件夹")
        self.select_save_folder_button.clicked.connect(self.select_save_folder)
        self.layout.addWidget(self.select_save_folder_button)

        self.save_folder_path_label = QLabel("选择的保存文件夹路径：")
        self.layout.addWidget(self.save_folder_path_label)

        self.dist_coeffs_label = QLabel("畸变系数（5个值，英文逗号分隔）")
        self.layout.addWidget(self.dist_coeffs_label)

        self.dist_coeffs_input = QLineEdit()
        self.dist_coeffs_input.setPlaceholderText("示例：-0.1,0.2,-0.001,0.001,0.3")
        self.layout.addWidget(self.dist_coeffs_input)

        self.camera_matrix_label = QLabel("相机内参（9个值，英文逗号分隔）")
        self.layout.addWidget(self.camera_matrix_label)

        self.camera_matrix_input = QLineEdit()
        self.camera_matrix_input.setPlaceholderText("示例：1000,0,500,0,1000,500,0,0,1")
        self.layout.addWidget(self.camera_matrix_input)

        self.start_processing_button = QPushButton("开始畸变矫正")
        self.start_processing_button.clicked.connect(self.start_processing)
        self.layout.addWidget(self.start_processing_button)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.exit_button = QPushButton("退出")
        self.exit_button.clicked.connect(self.close_application)
        self.layout.addWidget(self.exit_button)

        self.save_folder_path = ""
        self.folder_path = ""  # Initialize folder_path attribute

        self.image_processor = None

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.folder_path = folder_path
            self.folder_path_label.setText("选择的文件夹路径：" + folder_path)
            QMessageBox.information(self, "完成", "选择文件夹已完成！")

    def select_save_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if folder_path:
            self.save_folder_path = folder_path
            self.save_folder_path_label.setText("选择的保存文件夹路径：" + folder_path)
            QMessageBox.information(self, "完成", "选择保存文件夹已完成！")

    def start_processing(self):
        if not self.folder_path:
            QMessageBox.warning(self, "警告", "请先选择文件夹！")
            return

        if not self.save_folder_path:
            QMessageBox.warning(self, "警告", "请先选择保存文件夹！")
            return

        dist_coeffs_text = self.dist_coeffs_input.text()
        camera_matrix_text = self.camera_matrix_input.text()

        try:
            dist_coeffs = [float(x.strip()) for x in dist_coeffs_text.split(',')]
            camera_matrix = [float(x.strip()) for x in camera_matrix_text.split(',')]
        except ValueError:
            QMessageBox.warning(self, "警告", "输入格式不正确，请检查输入！")
            return

        if len(dist_coeffs) != 5:
            QMessageBox.warning(self, "警告", "畸变系数的值数量不正确，请检查输入！")
            return

        if len(camera_matrix) != 9:
            QMessageBox.warning(self, "警告", "相机内参的值数量不正确，请检查输入！")
            return

        dist_coeffs = np.array(dist_coeffs)
        camera_matrix = np.array(camera_matrix).reshape(3, 3)

        self.image_processor = ImageProcessor(self.folder_path, self.save_folder_path, dist_coeffs, camera_matrix)
        self.image_processor.progress_update.connect(self.update_progress)
        self.image_processor.finished.connect(self.processing_finished)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.image_processor.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self):
        self.progress_bar.hide()
        QMessageBox.information(self, "完成", "图像处理完成！")

    def close_application(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageUndistortionGUI()
    window.show()
    sys.exit(app.exec_())





    
    
    


