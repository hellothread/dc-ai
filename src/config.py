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
            'MaxDelay': '100',
            'Deepseek_API_Key': 'YOUR_DEEPSEEK_API_KEY',
            'Extra_Prompt': 'YOUR_EXTRA_PROMPT'
        }
        with open('config.ini', 'w', encoding='utf-8') as f:
            self.config.write(f)
        log_message("已创建默认配置文件 config.ini", "WARNING")
