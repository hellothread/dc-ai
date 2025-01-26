import os
import random
import time
import uuid
import configparser
from datetime import datetime
from colorama import Fore, init
import requests
from openai import OpenAI

# 初始化颜色输出
init(autoreset=True)

def log_message(message, status="INFO"):
    """增强型日志记录"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

class DiscordConfig:
    """配置管理类"""
    def __init__(self):
        self.config = configparser.ConfigParser()
        self._load_config()
        
        # 从配置文件读取参数
        self.channel_id = "984941796272521229"
        self.min_delay = 60
        self.max_delay = 100
        self.deepseek_api_key = self.config.get('SETTINGS', 'deepseek_api_key', fallback='')

        # 其他凭证读取
        self.token = ""
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
                parts = f.read().strip().split(':')
                if len(parts) != 4:
                    raise ValueError("代理格式错误")
                ip, port, user, pwd = parts
                return {
                    'http': f"http://{user}:{pwd}@{ip}:{port}",
                    'https': f"http://{user}:{pwd}@{ip}:{port}"
                }
        except Exception as e:
            log_message(f"代理配置异常: {str(e)}", "WARNING")
            return None


class DiscordSender:
    def __init__(self, config):
        self.config = config
        self.headers = {
            'Authorization': config.token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.max_retries = 3
        # 初始化 DeepSeek 客户端
        self.deepseek_client = OpenAI(
            api_key=config.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )

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
                log_message(f"消息发送成功: {content}", "SUCCESS")
                return response.json()['id']
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 30)
                log_message(f"触发速率限制，等待 {retry_after} 秒", "WARNING")
                time.sleep(retry_after)
        
            else:
                log_message(f"发送失败 [{response.status_code}]: {response.text}", "ERROR")
        except requests.exceptions.ConnectionError as e:
            log_message(f"连接错误: {str(e)}", "WARNING")
            time.sleep(5)
        except Exception as e:
            log_message(f"请求异常: {str(e)}", "ERROR")
        
       
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
                log_message(f"成功获取 {len(messages)} 条消息记录", "SUCCESS")
                return messages
            else:
                log_message(f"获取消息失败 [{response.status_code}]: {response.text}", "ERROR")
                return None
        except Exception as e:
            log_message(f"获取消息异常: {str(e)}", "ERROR")
            return None

    def process_with_deepseek(self, messages):
        try:
            message_text = "\n".join([f"{msg['author']['username']}: {msg['content']}" 
                                    for msg in messages if msg['content']])
        
            
            system_prompt = """你是一个Web3社区的Discord用户。
            现在的项目叫linera
            1. 检测到中文时用中文回复，英文时用英文回复
            2. 使用Web3社区常见用语，但不要过度使用
            3. 回复要简短自然，像真实用户一样
            4. 回复长度控制在15字以内
            5. 偶尔适当使用的Web3术语和表达：
               中文：项目靠谱,  生态, 社区
               英文：gm, ser, lfg, fren，nice project
            6. 禁止以下类型回复：
               - 机器人式问候
               - 过于正式的语气
               - 销售或推广式回复
            7. 回复要自然随意，像社区老友闲聊"""
            
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"基于以下对话生成一个自然的回复：\n{message_text}"}
                ],
                stream=False
            )
            
            reply = response.choices[0].message.content
            log_message("  ---- AI生成回复完成 ", reply)
            return reply
        except Exception as e:
            log_message(f"AI处理异常: {str(e)}", "ERROR")
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
                log_message(f"AI回复发送成功: {content}", "SUCCESS")
                return True
            else:
                log_message(f"AI回复发送失败 [{response.status_code}]: {response.text}", "ERROR")
                return False
        except Exception as e:
            log_message(f"发送异常: {str(e)}", "ERROR")
            return False

    def run(self):
        """运行主循环"""
        log_message("聊天机器人启动", "SUCCESS")
        log_message(f"当前配置: 频道ID={self.config.channel_id} 延迟={self.config.min_delay}-{self.config.max_delay}秒", "INFO")
        
        while True:
            # 获取频道消息
            messages = self.get_channel_messages(limit=1)
            if messages:
                # 使用DeepSeek生成回复
                ai_reply = self.process_with_deepseek(messages)
                if ai_reply:
                    # 发送AI生成的回复
                    self.send_ai_message(ai_reply)
            
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
            log_message(f"下次检查将在 {delay:.1f} 秒后", "INFO")
            time.sleep(delay)


if __name__ == "__main__":
    try:
        config = DiscordConfig()
        bot = DiscordSender(config)
        bot.run()
    except KeyboardInterrupt:
        log_message("程序已手动终止", "WARNING")