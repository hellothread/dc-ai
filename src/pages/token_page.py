from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit

class TokenPage(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.token_file = 'tokens.txt'  # Token数据文件
        self.init_ui()
        self.load_tokens()  # 加载已保存的Token

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

    def load_tokens(self):
        """从文件加载Token列表"""
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                for line in f:
                    name, token = line.strip().split(',')
                    self.add_token_to_table(name, token)
        except FileNotFoundError:
            pass  # 如果文件不存在，就创建一个空文件
            with open(self.token_file, 'w', encoding='utf-8') as f:
                pass

    def add_token_to_table(self, name, token):
        """添加Token到表格"""
        row_position = self.token_table.rowCount()
        self.token_table.insertRow(row_position)
        self.token_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(name))
        self.token_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(token))

    def save_tokens(self):
        """保存Token列表到文件"""
        with open(self.token_file, 'w', encoding='utf-8') as f:
            for row in range(self.token_table.rowCount()):
                name = self.token_table.item(row, 0).text()
                token = self.token_table.item(row, 1).text()
                f.write(f"{name},{token}\n")

    def add_auth(self):
        name = self.name_input.text().strip()
        token = self.token_input.text().strip()
        if name and token:
            self.add_token_to_table(name, token)
            self.name_input.clear()
            self.token_input.clear()
            self.save_tokens()  # 保存到文件
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请填写名称和Token")

    def import_auth(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入AUTH文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    name, token = line.strip().split(',')
                    self.add_token_to_table(name, token)
            self.save_tokens()  # 保存到文件

    def delete_auth(self):
        selected = self.token_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.token_table.removeRow(row)
            self.save_tokens()  # 保存到文件
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择要删除的AUTH") 