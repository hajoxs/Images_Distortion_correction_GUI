import os
import sys
import cv2
import numpy as np
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QLineEdit, QProgressBar, QMessageBox, QListWidget, QMenu
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class VideoProcessor(QThread):
    progress_update = pyqtSignal(int)
    processing_finished = pyqtSignal(str)

    def __init__(self, video_path, save_path, dist_coeffs, camera_matrix):
        super().__init__()
        self.video_path = video_path
        self.save_path = save_path
        self.dist_coeffs = dist_coeffs
        self.camera_matrix = camera_matrix

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            QMessageBox.warning(None, "警告", f"视频文件 {self.video_path} 无法打开！")
            return

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Specify a codec that is supported
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Change to XVID or another supported codec

        # Create VideoWriter object
        out = cv2.VideoWriter(self.save_path, fourcc, fps, (width, height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Undistort frame
            frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)

            # Write frame to output video
            out.write(frame)

            frame_count += 1
            progress = int(frame_count * 100 / total_frames)
            self.progress_update.emit(progress)

        cap.release()
        out.release()
        self.processing_finished.emit(self.save_path)

class VideoDistortionCorrectionGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("视频畸变矫正")
        self.setGeometry(100, 100, 400, 750)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.select_videos_button = QPushButton("选择视频文件")
        self.select_videos_button.clicked.connect(self.select_videos)
        self.layout.addWidget(self.select_videos_button)

        self.video_paths_list = QListWidget()
        self.video_paths_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.video_paths_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.video_paths_list.customContextMenuRequested.connect(self.show_context_menu)
        self.video_paths_list.itemClicked.connect(self.display_video_info)
        self.video_paths_list.keyPressEvent = self.handle_key_press_event
        self.layout.addWidget(self.video_paths_list)

        self.video_info_label = QLabel("当前视频信息：")
        self.layout.addWidget(self.video_info_label)

        self.select_save_dir_button = QPushButton("选择保存目录")
        self.select_save_dir_button.clicked.connect(self.select_save_dir)
        self.layout.addWidget(self.select_save_dir_button)

        self.save_dir_label = QLabel("选择的保存目录：")
        self.layout.addWidget(self.save_dir_label)

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

        # Progress Bars
        self.total_progress_label = QLabel("总进度条:")
        self.layout.addWidget(self.total_progress_label)

        self.total_progress_bar = QProgressBar()
        self.layout.addWidget(self.total_progress_bar)
        self.total_progress_bar.hide()

        self.current_progress_label = QLabel("当前视频进度条:")
        self.layout.addWidget(self.current_progress_label)

        self.current_progress_bar = QProgressBar()
        self.layout.addWidget(self.current_progress_bar)
        self.current_progress_bar.hide()

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.exit_button = QPushButton("退出")
        self.exit_button.clicked.connect(self.close_application)
        self.layout.addWidget(self.exit_button)

        self.save_dir = ""
        self.video_paths = []
        self.video_processors = []
        self.current_processor = None
        self.total_videos = 0

    def select_videos(self):
        video_paths, _ = QFileDialog.getOpenFileNames(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if video_paths:
            self.video_paths.extend(video_paths)
            self.video_paths_list.clear()
            self.video_paths_list.addItems(self.video_paths)
            QMessageBox.information(self, "完成", "选择视频文件已完成！")

    def select_save_dir(self):
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", "")
        if save_dir:
            self.save_dir = save_dir
            self.save_dir_label.setText("选择的保存目录：" + save_dir)
            QMessageBox.information(self, "完成", "选择保存目录已完成！")

    def show_context_menu(self, position):
        menu = QMenu()
        remove_action = menu.addAction("删除")
        action = menu.exec_(self.video_paths_list.viewport().mapToGlobal(position))
        if action == remove_action:
            self.delete_selected_items()

    def handle_key_press_event(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_items()
        else:
            QListWidget.keyPressEvent(self.video_paths_list, event)

    def delete_selected_items(self):
        selected_items = self.video_paths_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.video_paths.remove(item.text())
            self.video_paths_list.takeItem(self.video_paths_list.row(item))

    def display_video_info(self, item):
        video_path = item.text()
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_info_label.setText(f"当前视频信息：\n路径: {video_path}\n分辨率: {width}x{height}\n帧率: {fps} fps")
        else:
            self.video_info_label.setText("无法打开视频文件！")
        cap.release()

    def start_processing(self):
        if not self.video_paths:
            QMessageBox.warning(self, "警告", "请先选择视频文件！")
            return

        if not self.save_dir:
            QMessageBox.warning(self, "警告", "请先选择保存目录！")
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

        self.total_videos = len(self.video_paths)
        self.total_progress_bar.setMaximum(self.total_videos)
        self.total_progress_bar.setValue(0)
        self.total_progress_bar.show()

        self.current_progress_bar.setMaximum(100)
        self.current_progress_bar.setValue(0)
        self.current_progress_bar.show()

        for video_path in self.video_paths:
            save_path = os.path.join(self.save_dir, os.path.basename(video_path))
            video_processor = VideoProcessor(video_path, save_path, dist_coeffs, camera_matrix)
            video_processor.progress_update.connect(self.update_current_progress)
            video_processor.processing_finished.connect(self.video_processing_finished)
            self.video_processors.append(video_processor)
            self.current_processor = video_processor
            video_processor.start()

    def update_current_progress(self, value):
        if self.current_processor:
            self.current_progress_bar.setValue(value)

    def video_processing_finished(self, save_path):
        self.total_progress_bar.setValue(self.total_progress_bar.value() + 1)
        if self.total_progress_bar.value() >= self.total_videos:
            QMessageBox.information(self, "完成", "所有视频处理完成！")
        self.current_progress_bar.setValue(0)

    def close_application(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = VideoDistortionCorrectionGUI()
    gui.show()
    sys.exit(app.exec_())
