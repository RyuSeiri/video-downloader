import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import platform


class DownloadThread(QThread):
    progress_signal = pyqtSignal(float, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, format_id, save_path):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.save_path = save_path

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percentage = (d['downloaded_bytes'] / d['total_bytes']
                          ) * 100 if 'total_bytes' in d else 0
            self.progress_signal.emit(percentage, d['_percent_str'])
        elif d['status'] == 'finished':
            self.progress_signal.emit(100, '100%')

    def run(self):
        try:
            ydl_opts = {
                'format': self.format_id,
                'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                self.finished_signal.emit(filename)
        except Exception as e:
            self.error_signal.emit(str(e))


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_windows = platform.system() == 'Windows'
        self.downloads_path = os.path.join(
            os.path.expanduser('~'), 'Downloads')
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Video Downloader')
        self.setMinimumSize(600, 400)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel('Video Downloader')
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # URL Input
        url_group = QFrame()
        url_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
        url_layout = QVBoxLayout(url_group)
        url_layout.setContentsMargins(15, 15, 15, 15)

        url_label = QLabel('Video URL')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            'youtube, tiktok, x, bilibili url etc.')
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #0078D4;
            }
        """)

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addWidget(url_group)

        # Format Selection
        format_group = QFrame()
        format_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
        format_layout = QVBoxLayout(format_group)
        format_layout.setContentsMargins(15, 15, 15, 15)

        format_label = QLabel('Quality')
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            'Best Quality',
            '1080p',
            '720p',
            '480p',
            '360p',
            'Audio Only (Best)',
            'Audio Only (128kbps)'
        ])
        # self.format_combo.setStyleSheet("""
        #     QComboBox {
        #         border: 1px solid #E0E0E0;
        #         border-radius: 8px;
        #         padding: 5px;
        #     }
        # """)

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addWidget(format_group)

        # Save Location
        path_group = QFrame()
        path_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
        path_layout = QVBoxLayout(path_group)
        path_layout.setContentsMargins(15, 15, 15, 15)

        path_label = QLabel('Save Location')
        path_selector = QHBoxLayout()
        self.path_display = QLabel(self.downloads_path)
        self.path_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 5px;
                padding: 0.2em;
                border: 1 solid #E0E0E0;
            }
        """) 
        path_button = QPushButton('Change')
        path_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #E0E0E0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        path_button.clicked.connect(self.select_path)

        path_selector.addWidget(self.path_display)
        path_selector.addWidget(path_button)
        path_layout.addWidget(path_label)
        path_layout.addLayout(path_selector)
        layout.addWidget(path_group)

        # Progress Section
        progress_group = QFrame()
        progress_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(15, 15, 15, 15)

        self.status_label = QLabel('Status: Ready')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 5px;
                padding: 0.2em;
                border: 1 solid #E0E0E0;
            }
         """)               
        self.download_button = QPushButton('Start Download')
        self.download_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006CBD;
            }
            QPushButton:pressed {
                background-color: #005BA1;
            }
            QPushButton:disabled {
                background-color: #CCE4F7;
            }
        """)
        self.download_button.clicked.connect(self.start_download)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.download_button)
        layout.addWidget(progress_group)

    def select_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            self.downloads_path,
            QFileDialog.ShowDirsOnly
        )
        if path:
            self.path_display.setText(path)

    def get_format_id(self):
        format_map = {
            0: 'bestvideo+bestaudio/best',
            1: 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            2: 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            3: 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            4: 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            5: 'bestaudio/best',
            6: 'bestaudio[abr<=128]/best'
        }
        return format_map[self.format_combo.currentIndex()]

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, 'Error', 'Please enter a URL')
            return

        self.download_button.setEnabled(False)
        self.download_button.setText('Downloading...')
        self.status_label.setText('Status: Preparing download...')

        self.download_thread = DownloadThread(
            url,
            self.get_format_id(),
            self.path_display.text()
        )
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.download_error)
        self.download_thread.start()

    def update_progress(self, percentage, status):
        # self.progress_bar.setValue(int(percentage))
        self.status_label.setText(f'Status: Downloading... {status}')

    def download_finished(self, filename):
        self.download_button.setEnabled(True)
        self.download_button.setText('Start Download')
        self.status_label.setText('Status: Download completed')
        QMessageBox.information(
            self,
            'Complete',
            f'Download completed\nSaved to: {filename}'
        )
        self.url_input.clear()

    def download_error(self, error):
        self.download_button.setEnabled(True)
        self.download_button.setText('Start Download')
        self.status_label.setText('Status: Error occurred')
        QMessageBox.critical(self, 'Error', f'Error:\n{error}')


def main():
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
