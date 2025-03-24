import requests
import random
import time
from openai import OpenAI  # 确保导入 OpenAI
from utils import generate_nonce, log_message  # 导入 log_message

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

    def run(self):
        self.log("聊天机器人启动", "SUCCESS")
        # 随机延时
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
        except requests.exceptions.RequestException as e:
            self.log(f"请求异常: {str(e)}", "ERROR")
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

    # 其他方法保持不变... 