import sys
import threading  # 确保导入 threading
from PyQt5 import QtWidgets
from pages import MainPage, SettingsPage, TokenPage, ProxyPage
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
        
        # 根据 tokens.txt 和 proxy.txt 初始化 bots 列表
        self.initialize_bots()
        
        # 创建选项卡
        self.notebook = QtWidgets.QTabWidget()
        self.main_page = MainPage(self.log_queue, self.start_bots, self.stop_bots)
        self.notebook.addTab(self.main_page, '运行日志')
        self.settings_page = SettingsPage(self.config)
        self.notebook.addTab(self.settings_page, '设置')
        self.token_page = TokenPage(self.config)
        self.notebook.addTab(self.token_page, 'DC_AUTH')
        self.proxy_page = ProxyPage(self.config)  # 添加代理页
        self.notebook.addTab(self.proxy_page, '代理设置')
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.notebook)
        self.window.setLayout(layout)
        
        # 启动日志更新
        self.update_logs()  # 在初始化时就开始更新日志
    
    def initialize_bots(self):
        """根据 tokens.txt 和 proxy.txt 初始化 bots 列表"""
        try:
            # 读取tokens
            tokens = []
            try:
                with open('tokens.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        name, token = line.strip().split(',')
                        tokens.append(token)
            except FileNotFoundError:
                pass

            # 读取proxies
            proxies = []
            try:
                with open('proxy.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        proxy = line.strip()
                        if proxy:
                            proxies.append(proxy)
            except FileNotFoundError:
                pass

            # 确保每个token都有对应的proxy
            for i, token in enumerate(tokens):
                # 如果proxy数量不足，使用最后一个proxy
                proxy = proxies[i] if i < len(proxies) else proxies[-1] if proxies else None
                bot = DiscordSender(self.config, self.log_queue, token, i + 1, proxy)
                self.bots.append(bot)

        except Exception as e:
            self.log_queue.write(f"初始化bots时发生错误: {str(e)}", "ERROR")

    def start_bots(self):
        # 检查是否有token
        try:
            with open('tokens.txt', 'r', encoding='utf-8') as f:
                if not f.read().strip():
                    QtWidgets.QMessageBox.warning(self.window, "警告", "请先添加Token")
                    return
        except FileNotFoundError:
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