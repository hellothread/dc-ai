from queue import Queue
from datetime import datetime

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