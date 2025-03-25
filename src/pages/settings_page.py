from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit
from config import DiscordConfig

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
            ("最大延迟(秒):", "maxdelay")
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
            
            with open('config.ini', 'w', encoding='utf-8') as f:
                self.config.config.write(f)
            
            QtWidgets.QMessageBox.information(self, "成功", "设置已保存")
            self.config = DiscordConfig()  # 重新加载配置

        btn_layout = QHBoxLayout()
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(save_settings)
        btn_layout.addWidget(save_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout) 