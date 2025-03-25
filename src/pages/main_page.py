from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from utils import log_message

class MainPage(QtWidgets.QWidget):
    def __init__(self, log_queue, start_bots_callback, stop_bots_callback):
        super().__init__()
        self.log_queue = log_queue
        self.start_bots_callback = start_bots_callback
        self.stop_bots_callback = stop_bots_callback
        
        self.init_ui()
        self.start_log_update()  # 启动日志更新

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        control_frame = QHBoxLayout()
        self.start_button = QPushButton("启动所有")
        self.start_button.clicked.connect(self.start_bots_callback)
        control_frame.addWidget(self.start_button)

        self.stop_button = QPushButton("停止所有")
        self.stop_button.clicked.connect(self.stop_bots_callback)
        self.stop_button.setDisabled(True)
        control_frame.addWidget(self.stop_button)

        layout.addLayout(control_frame)
        self.setLayout(layout)

    def start_log_update(self):
        """定期更新日志显示"""
        self.update_logs()
        QtCore.QTimer.singleShot(1000, self.start_log_update)  # 每秒更新一次

    def update_logs(self):
        logs = self.log_queue.get_logs()
        for log in logs:
            message = f"[{log['timestamp']}] [{log['status']}] {log['message']}"
            self.log_text.append(message)  # 使用 append 方法添加新日志 