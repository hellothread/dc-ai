import sys
import threading  # 确保导入 threading
from PyQt5 import QtWidgets
from pages import MainPage, SettingsPage, TokenPage
from discord_sender import DiscordSender
from log_queue import LogQueue
from config import DiscordConfig

class ModernDiscordBotGUI:
    def __init__(self):
        self.app = QtWidgets.QApplication([])  # 初始化 PyQt5 应用
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("DC-AI-BOT - by Thread")
        self.window.setGeometry(100, 100, 700, 500)

        self.log_queue = LogQueue()
        self.bots = []  # 初始化为空列表
        self.config = DiscordConfig()
        
        # 根据 tokens.json 初始化 bots 列表
        self.initialize_bots()
        
        # 创建选项卡
        self.notebook = QtWidgets.QTabWidget()
        self.main_page = MainPage(self.log_queue, self.start_bots, self.stop_bots)
        self.notebook.addTab(self.main_page, '运行日志')
        self.settings_page = SettingsPage(self.config)
        self.notebook.addTab(self.settings_page, '设置')
        self.token_page = TokenPage(self.config)
        self.notebook.addTab(self.token_page, 'DC_AUTH')
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.notebook)
        self.window.setLayout(layout)
        
        # 启动日志更新
        self.update_logs()  # 在初始化时就开始更新日志
    
    def initialize_bots(self):
        """根据 tokens.json 初始化 bots 列表"""
        for index, token in enumerate(self.config.tokens["tokens"]):
            # 仅初始化，不启动
            bot = DiscordSender(self.config, self.log_queue, token, index + 1)
            self.bots.append(bot)

    def start_bots(self):
        if not self.config.tokens["tokens"]:
            QtWidgets.QMessageBox.warning(self.window, "警告", "请先添加Token")
            return
        
        for bot in self.bots:
            bot.stop_flag = False
        
        self.main_page.start_button.setDisabled(True)
        self.main_page.stop_button.setEnabled(True)
        
        for bot in self.bots:
            thread = threading.Thread(target=bot.run)  # 使用 threading
            thread.daemon = True
            thread.start()
        
        self.log_queue.write("所有机器人已启动", "SUCCESS")
    
    def stop_bots(self):
        for bot in self.bots:
            self.log_queue.write(f"正在停止bot: {bot.token[:20]}...", "INFO")
            bot.stop_flag = True
        self.log_queue.write("所有bot已停止", "SUCCESS")
        
        self.main_page.start_button.setEnabled(True)
        self.main_page.stop_button.setDisabled(True)

    def update_logs(self):
        self.main_page.update_logs()  # 调用主页面的更新日志方法

    def run(self):
        self.window.show()
        self.app.exec_()  # 启动 PyQt5 应用

if __name__ == "__main__":
    try:
        gui = ModernDiscordBotGUI()
        gui.run()
    except Exception as e:
        print(f"发生错误: {e}")
        input("按回车键退出...") 