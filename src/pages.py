from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QListWidget
from config import DiscordConfig  # 导入 DiscordConfig
from utils import log_message  # 导入 log_message

class MainPage(QtWidgets.QWidget):
    def __init__(self, log_queue, start_bots_callback, stop_bots_callback):
        super().__init__()
        self.log_queue = log_queue
        self.start_bots_callback = start_bots_callback
        self.stop_bots_callback = stop_bots_callback
        
        self.init_ui()

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

    def update_logs(self):
        max_length = 82  # 设置最大字符长度
        
        while not self.log_queue.queue.empty():
            log = self.log_queue.queue.get()
            message = f"[{log['timestamp']}] [{log['status']}] {log['message']}"
            
            # 如果消息长度超过最大长度，则截断并添加省略号
            if len(message) > max_length:
                message = message[:max_length - 3] + "..."
            
            self.log_text.setPlainText(self.log_text.toPlainText() + message + "\n")
            
            # 如果是INFO日志，添加一个额外的空行
            if log['status'].strip() == "INFO":
                self.log_text.setPlainText(self.log_text.toPlainText() + "\n")
            
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

class SettingsPage(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        settings = [
            ("DeepSeek Key:", "deepseek_api_key"),
            ("DC频道 ID:", "channelid"),
            ("最小延迟(秒):", "mindelay"),
            ("最大延迟(秒):", "maxdelay"),
            ("代理设置 (格式: ip:port:user:password):", "proxy")  # 添加代理设置
        ]
        
        self.setting_vars = {}
        for label, key in settings:
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(label))
            var = str(self.config.config.get('SETTINGS', key, fallback=''))
            self.setting_vars[key] = var
            line_edit = QLineEdit(var)
            h_layout.addWidget(line_edit)
            layout.addLayout(h_layout)
        
        extra_prompt_text = QTextEdit()
        extra_prompt_text.setPlainText(self.config.config.get('SETTINGS', 'extra_prompt', fallback=''))
        layout.addWidget(extra_prompt_text)

        def save_settings():
            for key, var in self.setting_vars.items():
                self.config.config.set('SETTINGS', key, var)
            self.config.config.set('SETTINGS', 'extra_prompt', extra_prompt_text.toPlainText().strip())
            
            # 保存代理设置到 proxy.txt
            proxy_value = self.setting_vars['proxy']
            with open('proxy.txt', 'w', encoding='utf-8') as f:
                f.write(proxy_value.strip())
            
            with open('config.ini', 'w', encoding='utf-8') as f:
                self.config.config.write(f)
            
            # 添加调试信息
            print("设置已保存：", {key: self.config.config.get('SETTINGS', key) for key in self.setting_vars.keys()})
            
            # 确认 DeepSeek Key 是否被正确保存
            print("DeepSeek Key:", self.config.config.get('SETTINGS', 'deepseek_api_key'))
            
            QtWidgets.QMessageBox.information(self, "成功", "设置已保存")
            self.config = DiscordConfig()  # 重新加载配置

        btn_layout = QHBoxLayout()
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(save_settings)
        btn_layout.addWidget(save_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

class TokenPage(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.token_listbox = QListWidget()
        self.token_listbox.addItems(self.config.tokens["tokens"])
        layout.addWidget(self.token_listbox)
        
        btn_frame = QHBoxLayout()
        add_button = QPushButton("添加AUTH")
        btn_frame.addWidget(add_button)
        delete_button = QPushButton("删除AUTH")
        btn_frame.addWidget(delete_button)
        layout.addLayout(btn_frame)

        self.setLayout(layout) 