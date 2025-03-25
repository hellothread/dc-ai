from PyQt5 import QtWidgets, QtCore
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
        
        # 创建 QTableWidget
        self.token_table = QtWidgets.QTableWidget()
        self.token_table.setColumnCount(2)  # 两列：名称、Token
        self.token_table.setHorizontalHeaderLabels(["名称", "Token"])
        
        # 设置最后一列占满剩余空间
        self.token_table.horizontalHeader().setStretchLastSection(True)
        self.token_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)  # 使 Token 列占满剩余空间
        
        layout.addWidget(self.token_table)

        # 添加名称和 Token 的输入框
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入名称")
        layout.addWidget(self.name_input)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("输入Token")
        layout.addWidget(self.token_input)

        btn_frame = QHBoxLayout()
        add_button = QPushButton("添加AUTH")
        add_button.clicked.connect(self.add_auth)
        btn_frame.addWidget(add_button)

        import_button = QPushButton("导入AUTH")
        import_button.clicked.connect(self.import_auth)
        btn_frame.addWidget(import_button)

        delete_button = QPushButton("删除AUTH")
        delete_button.clicked.connect(self.delete_auth)
        btn_frame.addWidget(delete_button)

        layout.addLayout(btn_frame)
        self.setLayout(layout)

    def add_auth(self):
        name = self.name_input.text().strip()
        token = self.token_input.text().strip()
        if name and token:
            row_position = self.token_table.rowCount()
            self.token_table.insertRow(row_position)  # 插入新行
            self.token_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(name))  # 名称
            self.token_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(token))  # Token
            self.name_input.clear()
            self.token_input.clear()
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请填写名称和Token")

    def import_auth(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入AUTH文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    name, token = line.strip().split(',')
                    row_position = self.token_table.rowCount()
                    self.token_table.insertRow(row_position)  # 插入新行
                    self.token_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(name))  # 名称
                    self.token_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(token))  # Token

    def delete_auth(self):
        selected = self.token_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.token_table.removeRow(row)
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择要删除的AUTH")

class ProxyPage(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.proxy_listbox = QListWidget()
        layout.addWidget(self.proxy_listbox)

        # 添加代理的输入框
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("输入代理 (格式: ip:port:user:password)")
        layout.addWidget(self.proxy_input)

        btn_frame = QHBoxLayout()
        add_proxy_button = QPushButton("添加代理")
        add_proxy_button.clicked.connect(self.add_proxy)
        btn_frame.addWidget(add_proxy_button)

        import_proxy_button = QPushButton("导入代理")
        import_proxy_button.clicked.connect(self.import_proxy)
        btn_frame.addWidget(import_proxy_button)

        layout.addLayout(btn_frame)
        self.setLayout(layout)

    def add_proxy(self):
        proxy = self.proxy_input.text().strip()
        if proxy:
            self.proxy_listbox.addItem(proxy)
            self.proxy_input.clear()
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请填写代理信息")

    def import_proxy(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入代理文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    self.proxy_listbox.addItem(line.strip()) 