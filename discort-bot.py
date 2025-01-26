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
        self.stop_flag = False
        
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
            message_text = "\n".join([f"{msg['author']['username']}: {msg['content']}" for msg in messages if msg['content']])
            

            system_prompt = """你是一个真实的Web3社区活跃成员，性格设定如下：

个人背景：
- 25-35岁的年轻技术爱好者
- 对区块链和加密货币有深入了解
- 经常活跃在Discord社区，熟悉社区文化

交流风格：
- 语气随意但不失专业感
- 喜欢使用俚语和社区黑话
- 回复节奏快，信息密度高
- 带有轻微的技术极客特征

语言特点：
- 英文回答
- 偶尔表情符号和缩写
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
- 体现对Web3文化的理解"""


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
        """运行主循环"""
        self.log("聊天机器人启动", "SUCCESS")
        
        while not self.stop_flag:
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
            time.sleep(delay)

class DiscordBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DC-AI-BOT - by Thread")
        self.root.geometry("600x500")
        
        self.log_queue = LogQueue()
        self.bots = []
        self.config = DiscordConfig()
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # 创建主页、设置页和Token管理页
        self.setup_main_page()
        self.setup_settings_page()
        self.setup_token_page()
        
        # 启动日志更新
        self.update_logs()  # 在初始化时就开始更新日志
    
    def setup_main_page(self):
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text='运行日志')
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(main_frame, height=30)
        self.log_text.pack(expand=True, fill='both', padx=5, pady=5)
        self.log_text.config(state='disabled')  # 设置为只读
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="启动所有", command=self.start_bots).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="停止所有", command=self.stop_bots).pack(side=tk.LEFT, padx=5)
    
    def setup_settings_page(self):
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='设置')
        
        # 创建设置项
        settings = [
            ("DeepSeek Key:", "deepseek_api_key"),
            ("DC频道 ID:", "channelid"),
            ("最小延迟(秒):", "mindelay"),
            ("最大延迟(秒):", "maxdelay")
        ]
        
        self.setting_vars = {}
        for i, (label, key) in enumerate(settings):
            ttk.Label(settings_frame, text=label).grid(row=i, column=0, padx=10, pady=10, sticky='e')
            var = tk.StringVar(value=self.config.config.get('SETTINGS', key, fallback=''))
            self.setting_vars[key] = var
            ttk.Entry(settings_frame, textvariable=var, width=50).grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        
        # 添加多行文本框用于额外Prompt
        ttk.Label(settings_frame, text="额外 AI Prompt:").grid(row=len(settings), column=0, padx=10, pady=10, sticky='ne')
        extra_prompt_text = tk.Text(settings_frame, height=10, width=50)
        extra_prompt_text.grid(row=len(settings), column=1, padx=5, pady=5, sticky='ew')
        extra_prompt_text.insert('1.0', self.config.config.get('SETTINGS', 'extra_prompt', fallback=''))
        
        def save_settings():
            for key, var in self.setting_vars.items():
                self.config.config.set('SETTINGS', key, var.get())
            # 保存多行文本框内容
            self.config.config.set('SETTINGS', 'extra_prompt', extra_prompt_text.get('1.0', 'end').strip())
            
            with open('config.ini', 'w', encoding='utf-8') as f:
                self.config.config.write(f)
            
            messagebox.showinfo("成功", "设置已保存")
            self.config = DiscordConfig()  # 重新加载配置
        
        ttk.Button(settings_frame, text="保存设置", command=save_settings).grid(row=len(settings)+1, column=0, columnspan=3, pady=20)
        
    def setup_token_page(self):
        token_frame = ttk.Frame(self.notebook)
        self.notebook.add(token_frame, text='Token管理')
        
        # 增加Listbox宽度
        self.token_listbox = tk.Listbox(token_frame, height=20, width=50)
        self.token_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 刷新Token列表
        self.refresh_token_list()
        
        # 控制按钮
        btn_frame = ttk.Frame(token_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加Token", command=self.add_token).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除Token", command=self.delete_token).pack(side=tk.LEFT, padx=5)
    
    def refresh_token_list(self):
        self.token_listbox.delete(0, tk.END)
        for token in self.config.tokens["tokens"]:
            self.token_listbox.insert(tk.END, token)  # 显示完整的Token
    
    def add_token(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加Token")
        dialog.geometry("400x150")
        
        ttk.Label(dialog, text="请输入Token").pack(pady=10)
        token_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=token_var, width=50).pack(pady=10)
        
        def submit():
            token = token_var.get().strip()
            if token:
                self.config.tokens["tokens"].append(token)
                with open('tokens.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config.tokens, f)
                self.refresh_token_list()
                
                # 启动新添加的Token对应的机器人
                self.start_bot(token, len(self.config.tokens["tokens"]))
        
        ttk.Button(dialog, text="确定", command=submit).pack(pady=10)
    
    def delete_token(self):
        selection = self.token_listbox.curselection()
        if selection:
            index = selection[0]
            
            # 停止与该Token相关的机器人
            bot, thread = self.bots[index]
            bot.stop_flag = True
            self.log_queue.write(f"机器人 {index + 1} 已停止", "INFO")
            self.bots.pop(index)
            
            # 删除Token
            self.config.tokens["tokens"].pop(index)
            with open('tokens.json', 'w', encoding='utf-8') as f:
                json.dump(self.config.tokens, f)
            self.refresh_token_list()
    
    def save_settings(self):
        for key, var in self.setting_vars.items():
            self.config.config.set('SETTINGS', key, var.get())
        
        with open('config.ini', 'w', encoding='utf-8') as f:
            self.config.config.write(f)
        
        messagebox.showinfo("成功", "设置已保存")
        self.config = DiscordConfig()  # 重新加载配置

    def start_bots(self):
        """启动所有机器人"""
        if not self.config.tokens["tokens"]:
            messagebox.showwarning("警告", "请先添加Token")
            return
            
        for index, token in enumerate(self.config.tokens["tokens"]):
            bot = DiscordSender(self.config, self.log_queue, token, index + 1)  # 传递Token编号
            
            # 固定延时1秒
            time.sleep(1.4)
            
            thread = threading.Thread(target=bot.run)
            thread.daemon = True
            thread.start()
            self.bots.append((bot, thread))
        
        self.log_queue.write("所有机器人已启动", "SUCCESS")
    
    def stop_bots(self):
        for bot, _ in self.bots:
            self.log_queue.write(f"正在停止bot: {bot.token[:20]}...", "INFO")
            bot.stop_flag = True
        self.bots.clear()
        self.log_queue.write("所有bot已停止", "SUCCESS")
    
    def update_logs(self):
        """更新日志显示"""
        while not self.log_queue.queue.empty():
            log = self.log_queue.queue.get()
            self.log_text.config(state='normal')  # 临时允许编辑
            self.log_text.insert(tk.END, 
                f"[{log['timestamp']}] [{log['status']}] {log['message']}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')  # 恢复只读
        self.root.after(100, self.update_logs)
    
    def run(self):
        self.root.mainloop()

    def start_bot(self, token, token_index):
        """启动单个机器人"""
        bot = DiscordSender(self.config, self.log_queue, token, token_index)
        thread = threading.Thread(target=bot.run)
        thread.daemon = True
        thread.start()
        self.bots.append((bot, thread))
        self.log_queue.write(f"机器人 {token_index} 已启动", "SUCCESS")

if __name__ == "__main__":
    try:
        gui = DiscordBotGUI()
        gui.run()
    except Exception as e:
        print(f"发生错误: {e}")
        input("按回车键退出...")
