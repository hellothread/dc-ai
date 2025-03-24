import configparser
import json
import os
from utils import log_message  # 导入 log_message

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
        else:
            # 添加调试信息
            print("加载的配置：", {key: self.config.get('SETTINGS', key) for key in self.config['SETTINGS']})

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