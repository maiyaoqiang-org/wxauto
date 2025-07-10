from wxauto import WeChat
import requests  # 新增导入
import csv
import os
from datetime import datetime

from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
import queue
import threading
wx = WeChat()
# 创建消息队列和处理线程
message_queue = queue.Queue()

# 创建日志目录
LOG_DIR = "chats.log"
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    print("\n--- Iterating through attributes and types ---")
    for attr_name in dir(msg):
        # 过滤掉特殊方法和属性，只关注用户定义的属性和方法
        if not attr_name.startswith('__'):
            attr_value = getattr(msg, attr_name)
            print(f"Attribute: {attr_name}, Value: {attr_value}, Type: {type(attr_value)}")

def process_messages():
    while True:
        msg, chat = message_queue.get()
        try:
           on_message(msg,chat)
        finally:
            message_queue.task_done()


def get_reply_content(msg_content):
    api_url = "https://maiyaoqiang.fun/api/openai/chat/1"
    payload = {"content": msg_content}
    try:
        response = requests.post(api_url, json=payload)
        response_data = response.json()

        if response.status_code in (200, 201):
            reply_content = response_data.get("replyContent", "收到消息")
            if not reply_content:
                reply_content = response_data.get("replyContent", "收到消息")
            return reply_content
        else:
            return response_data.get("replyContent", "处理消息时出错")

    except Exception as e:
        print(f"API调用出错: {e}")
        return "服务暂时不可用，请稍后再试"

def get_coze_reply_content(msg_content, chat):
    user_id = str(hash(chat.who))
    try:
        return coze_client.chat(user_id, msg_content)
    except Exception as e:
        print(f"调用Coze API出错: {e}")
        return "服务暂时不可用，请稍后再试"

def on_message(msg, chat):
    try:
        # 记录所有消息
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message_to_csv(msg, chat)
    except Exception as e:
        print(f"保存消息到CSV文件出错: {e}")


    current_nickname = wx.nickname
    if f"@{current_nickname}\u2005" in msg.content:
        sender_name = msg.sender
        try:
            print(f"调试4 - chat.who: {chat.who}")
            print(f"{chat.who} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{sender_name}:{msg.content}")
            print("=" * 30)

            try:
                if "coze回答" in msg.content:
                    reply_content = get_coze_reply_content(msg.content, chat)
                elif "api 回答" in msg.content:
                    reply_content = get_reply_content(msg.content)
                elif "测试群" in chat.who:
                    reply_content = get_coze_reply_content(msg.content,chat)
                elif "梦战测试群" in chat.who:
                    reply_content = get_reply_content(msg.content)
                else:
                    reply_content = get_reply_content(msg.content)
                
                print(f"调试5 - 准备引用回复: {reply_content}")
                msg.quote(reply_content)
                print("调试6 - 引用回复完成")
            except Exception as e:
                print(f"获取回复内容时出错: {e}")
                
        except Exception as e:
            print(f"打印日志时出错: {e}")

class CozeClient:
    def __init__(self, token: str, bot_id: str, base_url=COZE_CN_BASE_URL):
        self.client = Coze(auth=TokenAuth(token=token), base_url=base_url)
        self.bot_id = bot_id

    def chat(self, user_id: str, content: str) -> str:
        """
        与Coze聊天并获取完整回复
        :param user_id: 用户ID
        :param content: 聊天内容
        :return: 完整回复内容
        """
        full_response = ""
        for event in self.client.chat.stream(
            bot_id=self.bot_id,
            user_id=user_id,
            additional_messages=[
                Message.build_user_question_text(content),
            ],
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                full_response += event.message.content

        return full_response

# 初始化Coze客户端
COZE_API_TOKEN = 'pat_cwqlh4X5fvEdShfjghm0OSX4Qo5EnPrz93nYsbDLOTCkVe5c9lRdeU9F0WKn6DpV'
COZE_BOT_ID = '7524160519495270443'
coze_client = CozeClient(COZE_API_TOKEN, COZE_BOT_ID)

def save_message_to_csv(msg, chat):
    """保存消息到CSV文件，按群分组保存"""
    # 过滤系统消息
    if hasattr(msg, 'attr') and msg.attr == 'system':
        return
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取群组名称作为子目录
    group_name = chat.who.replace(" ", "_").replace("\\", "_").replace("/", "_")
    group_dir = os.path.join(LOG_DIR, group_name)
    os.makedirs(group_dir, exist_ok=True)
    
    # 获取当前小时作为文件名
    hour_str = datetime.now().strftime("%Y%m%d_%H")
    filename = f"{group_dir}/chat_{hour_str}.csv"
    
    # 文件字段
    fieldnames = ["timestamp", "sender", "content"]
    
    # 写入文件
    file_exists = os.path.exists(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow({
            "timestamp": timestamp,
            "sender": msg.sender,
            "content": msg.content
        })


# 需要监听的群组列表
GROUP_LIST = [
    # "测试群",
    # "梦战测试群", 
    "墨源梦战粉丝交流群",
    "墨源梦战交流群"
]

print("程序启动成功，开始监听...")
print(f"监听的群组: {GROUP_LIST}")

# 添加群组监听
for group_name in GROUP_LIST:
    wx.AddListenChat(nickname=group_name, callback=on_message)
# 保持程序运行
wx.KeepRunning()