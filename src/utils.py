import uuid
from datetime import datetime  # 导入 datetime
from colorama import Fore

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