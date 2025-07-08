from wxauto import WeChat
import requests  # 新增导入
from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
import queue
import threading
import datetime
wx = WeChat()
# 创建消息队列和处理线程
message_queue = queue.Queue()

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
            print(response_data)
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
    current_nickname = wx.nickname
    if f"@{current_nickname}\u2005" in msg.content:
        sender_name = msg.sender
        # 打印群名 用户名 用户回复信息  时间  弄好看点  打印如下
        # 群名 2025-07-08 10:10:10
        # 用户名: 内容
        print(f"{chat.who} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{sender_name}:{msg.content}")
        print("=" * 30)  # 分隔线

        if "coze回答" in msg.content:
            reply_content = get_coze_reply_content(msg.content, chat)
        elif "api 回答" in msg.content:
            reply_content = get_reply_content(msg.content, chat)
        elif "测试群" in chat.who:
            reply_content = get_reply_content(msg.content, chat)
        elif "梦战测试群" in chat.who:
            reply_content = get_coze_reply_content(msg.content, chat)
        else:
            reply_content = get_reply_content(msg.content)

        msg.quote(reply_content)

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

# 添加监听，监听到的消息用on_message函数进行处理
# 监听群名为"测试群"
wx.AddListenChat(nickname="测试群", callback=on_message)

wx.AddListenChat(nickname="梦战测试群", callback=on_message)

# 保持程序运行
wx.KeepRunning()
