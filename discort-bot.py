import os
import random
import time
import uuid
import configparser
from datetime import datetime
from colorama import Fore, init
import requests
from openai import OpenAI
from threading import Thread
from queue import Queue
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from datetime import datetime, time as dt_time
import tkinter.messagebox as messagebox
import threading
import ttkbootstrap as tb
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QListWidget, QTabWidget

# 初始化颜色输出
init(autoreset=True)

def log_message(message, status="INFO"):
    """增强型日志记录"""
    timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
    color_map = {
        "INFO": Fore.WHITE,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW
    }
    print(f"{Fore.BLUE}[{timestamp}] {color_map.get(status, Fore.WHITE)}[{status}] {message}")

def generate_nonce():
    """生成唯一消息标识符"""
    return str(uuid.uuid4().int)[:18]  # 生成18位数字nonce

class LogQueue:
    """日志队列管理"""
    def __init__(self):
        self.queue = Queue()
        
    def write(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
        # 将status格式化为固定长度，假设最大长度为7（如"SUCCESS"）
        formatted_status = f"{status:<7}"  # 左对齐，长度为7
        self.queue.put({
            "timestamp": timestamp,
            "status": formatted_status,
            "message": message
        })

class DiscordConfig:
    """配置管理类"""
    def __init__(self):
        self.config = configparser.ConfigParser()
        self._load_config()
        
        # 从配置文件读取参数
        self.channel_id = self.config.get('SETTINGS', 'channelid', fallback='')
        self.min_delay = self.config.getint('SETTINGS', 'mindelay', fallback=60)
        self.max_delay = self.config.getint('SETTINGS', 'maxdelay', fallback=100)
        self.deepseek_api_key = self.config.get('SETTINGS', 'deepseek_api_key', fallback='')
        
        # 读取tokens.json
        try:
            with open('tokens.json', 'r', encoding='utf-8') as f:
                self.tokens = json.load(f)
        except FileNotFoundError:
            self.tokens = {"tokens": []}
            with open('tokens.json', 'w', encoding='utf-8') as f:
                json.dump(self.tokens, f)

        # 其他凭证读取
        self.proxy = self._parse_proxy()
        
        

    def _load_config(self):
        """加载配置文件"""
        self.config.read('config.ini', encoding='utf-8')
        if not self.config.has_section('SETTINGS'):
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置文件"""
        self.config['SETTINGS'] = {
            'ChannelID': 'YOUR_CHANNEL_ID',
            'MinDelay': '60',
            'MaxDelay': '100'
        }
        with open('config.ini', 'w', encoding='utf-8') as f:
            self.config.write(f)
        log_message("已创建默认配置文件 config.ini", "WARNING")

    def _read_file(self, filename):
        """读取文本文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            log_message(f"文件不存在: {filename}", "ERROR")
            exit(1)

    def _parse_proxy(self):
        """解析代理配置"""
        try:
            with open('proxy.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    log_message("代理未配置，将不使用代理", "INFO")
                    return None
                
                parts = content.split(':')
                if len(parts) != 4 or not parts[0]:
                    log_message("代理格式错误，将不使用代理", "INFO")
                    return None
                
                ip, port, user, pwd = parts
                return {
                    'http': f"http://{user}:{pwd}@{ip}:{port}",
                    'https': f"http://{user}:{pwd}@{ip}:{port}"
                }
        except FileNotFoundError:
            # 如果文件不存在，创建一个空的proxy.txt
            open('proxy.txt', 'w', encoding='utf-8').close()
            log_message("已创建空的proxy.txt文件", "WARNING")
            return None
        except Exception as e:
            log_message(f"代理配置异常: {str(e)}", "WARNING")
            return None

class DiscordSender:
    def __init__(self, config, log_queue, token, token_index):
        self.config = config
        self.log_queue = log_queue
        self.token = token
        self.token_index = token_index  # 添加Token编号
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        self.max_retries = 3
        # 初始化 DeepSeek 客户端
        self.deepseek_client = OpenAI(
            api_key=config.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        self.stop_flag = False  # 确保初始值为False
        
        # 修改日志记录方式
        def custom_log(message, status="INFO"):
            """自定义日志记录"""
            log_message(f"Token {self.token_index}: {message}", status)  # 在日志中添加Token编号
            self.log_queue.write(f"[账号{self.token_index}] {message}", status)
        
        self.log = custom_log  # 使用自定义日志方法

    def _construct_payload(self, content):
        """构建消息体"""
        return {
            "content": content,
            "nonce": generate_nonce(),
            "tts": False,
            "flags": 0
        }

    def send_message(self):
        """发送消息"""
        try:
        
            content = random.choice(self.config.messages)
            payload = self._construct_payload(content)
            url = f"https://discord.com/api/v9/channels/{self.config.channel_id}/messages"

            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                proxies=self.config.proxy,
                timeout=30
            )

            if response.status_code == 200:
                self.log(f"消息发送成功: {content}", "SUCCESS")  # 使用新的日志方法
                return response.json()['id']
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 30)
                self.log(f"触发速率限制，等待 {retry_after} 秒", "WARNING")
                time.sleep(retry_after)
            else:
                self.log(f"发送失败 [{response.status_code}]: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"请求异常: {str(e)}", "ERROR")
        
        return None

    def get_channel_messages(self, limit=1):
        """获取频道消息历史"""
        try:
            url = f"https://discord.com/api/v9/channels/{self.config.channel_id}/messages"
            params = {'limit': limit}
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                proxies=self.config.proxy,
                timeout=30
            )

            if response.status_code == 200:
                messages = response.json()
                for msg in messages:
                    content = msg.get('content', '无内容')
                    self.log(f"[获取] {content}", "SUCCESS")
                return messages
            else:
                self.log(f"获取消息失败 [{response.status_code}]: {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"获取消息异常: {str(e)}", "ERROR")
            return None

    def process_with_deepseek(self, messages):
        try:
            # 仅提取消息内容，不包括用户名
            message_text = "\n".join([msg['content'] for msg in messages if msg['content']])
            
            system_prompt = """你是一个真实的Web3社区活跃成员，性格设定如下：

个人背景：
- 27岁的年轻技术爱好者
- 对区块链和加密货币有深入了解
- 经常活跃在Discord社区，熟悉社区文化

交流风格：
- 语气随意但不失专业感
- 喜欢使用俚语和社区黑话
- 回复节奏快，信息密度高
- 带有轻微的技术极客特征

语言特点：
- 英文回答
- 少用表情符号和缩写
- 回复简洁有力
- 根据对话氛围快速调整语气

禁忌行为：
- 绝不像营销号
- 不做无意义灌水
- 避免教科书式回复
- 拒绝过度解释

回复原则：
- 5-20字
- 优先使用有趣、生动的表达
- 体现个人态度和观点
- 增加互动感和社区归属感

特殊术语使用：
- gm/ser/lfg等社区用语要恰到好处
- 不生搬硬套，要有语境
- 体现对Web3文化的理解

生成指令：
- 避免重复使用相同的短语
- 尝试使用不同的表达方式
- 提供多样化的回复示例"""

            # 获取外部额外的prompt
            extra_prompt = self.config.config.get('SETTINGS', 'extra_prompt', fallback='')

            # 合并内部和外部prompt
            combined_prompt = f"""{system_prompt}

            {extra_prompt}"""

            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat", 
                messages=[
                    {"role": "system", "content": combined_prompt},
                    {"role": "user", "content": f"基于以下对话语境和氛围，生成一个自然流畅的回复：\n{message_text}"}
                ], 
                stream=False
            )
            
            reply = response.choices[0].message.content
            self.log(f"[生成] {reply}", "SUCCESS")
            return reply
        
        except Exception as e:
            self.log(f"AI处理异常: {str(e)}", "ERROR")
            return None


    def send_ai_message(self, content):
        """发送AI生成的消息"""
        payload = self._construct_payload(content)
        url = f"https://discord.com/api/v9/channels/{self.config.channel_id}/messages"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                proxies=self.config.proxy,
                timeout=30
            )

            if response.status_code == 200:
                self.log(f"[回复] {content}", "SUCCESS")
                return True
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 30)
                self.log(f"触发速率限制，等待 {retry_after} 秒", "WARNING")
                time.sleep(retry_after)
                # 重试发送消息
                return self.send_ai_message(content)
            else:
                self.log(f"AI回复发送失败 [{response.status_code}]: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"发送异常: {str(e)}", "ERROR")
            return False


    def run(self):
        self.log("聊天机器人启动", "SUCCESS")
        #随机延时
        delay = random.uniform(0, 5)
        time.sleep(delay)
        

        while not self.stop_flag:
            try:
                # 获取频道消息
                messages = self.get_channel_messages(limit=1)
                if messages:
                    # 使用DeepSeek生成回复
                    ai_reply = self.process_with_deepseek(messages)
                    if ai_reply:
                        # 发送AI生成的回复
                        self.send_ai_message(ai_reply)
                
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                self.log(f"[延时] 下次发送将在 {delay:.1f} 秒后", "INFO")
                
                # 每次循环检查停止标志
                if self.stop_flag:
                    break
                
                time.sleep(delay)
            except Exception as e:
                self.log(f"运行时异常: {str(e)}", "ERROR")
                break
        
        self.log("聊天机器人已停止", "INFO")

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
            
            QMessageBox.information(self, "成功", "设置已保存")
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
        self.notebook = QTabWidget()
        self.main_page = MainPage(self.log_queue, self.start_bots, self.stop_bots)
        self.notebook.addTab(self.main_page, '运行日志')
        self.settings_page = SettingsPage(self.config)
        self.notebook.addTab(self.settings_page, '设置')
        self.token_page = TokenPage(self.config)
        self.notebook.addTab(self.token_page, 'DC_AUTH')
        
        layout = QVBoxLayout()
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
            QMessageBox.warning(self.window, "警告", "请先添加Token")
            return
        
        for bot in self.bots:
            bot.stop_flag = False
        
        self.main_page.start_button.setDisabled(True)
        self.main_page.stop_button.setEnabled(True)
        
        for bot in self.bots:
            thread = threading.Thread(target=bot.run)
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
