from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit

class ProxyPage(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.proxy_file = 'proxy.txt'
        self.init_ui()
        self.load_proxies()  # 加载已保存的代理

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建表格
        self.proxy_table = QtWidgets.QTableWidget()
        self.proxy_table.setColumnCount(1)  # 一列：代理
        self.proxy_table.setHorizontalHeaderLabels(["代理"])
        
        # 设置列宽
        self.proxy_table.horizontalHeader().setStretchLastSection(True)  # 代理列占满剩余空间
        
        layout.addWidget(self.proxy_table)

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

        delete_proxy_button = QPushButton("删除代理")
        delete_proxy_button.clicked.connect(self.delete_proxy)
        btn_frame.addWidget(delete_proxy_button)

        layout.addLayout(btn_frame)
        self.setLayout(layout)

    def load_proxies(self):
        """从文件加载代理列表"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        self.add_proxy_to_table(proxy)
        except FileNotFoundError:
            pass  # 如果文件不存在，就创建一个空文件
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                pass

    def add_proxy_to_table(self, proxy):
        """添加代理到表格"""
        row = self.proxy_table.rowCount()
        self.proxy_table.insertRow(row)
        self.proxy_table.setItem(row, 0, QtWidgets.QTableWidgetItem(proxy))  # 代理

    def save_proxies(self):
        """保存代理列表到文件"""
        with open(self.proxy_file, 'w', encoding='utf-8') as f:
            for row in range(self.proxy_table.rowCount()):
                proxy = self.proxy_table.item(row, 0).text()
                f.write(proxy + '\n')

    def add_proxy(self):
        proxy = self.proxy_input.text().strip()
        if proxy:
            self.add_proxy_to_table(proxy)
            self.proxy_input.clear()
            self.save_proxies()  # 保存到文件
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请填写代理信息")

    def delete_proxy(self):
        selected = self.proxy_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.proxy_table.removeRow(row)
            self.save_proxies()  # 保存到文件
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择要删除的代理")

    def import_proxy(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入代理文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        self.add_proxy_to_table(proxy)
            self.save_proxies()  # 保存到文件 