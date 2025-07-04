from wxauto import WeChat
import time

wx = WeChat()

def log(msg):
    print("\n--- Iterating through attributes and types ---")
    for attr_name in dir(msg):
        # 过滤掉特殊方法和属性，只关注用户定义的属性和方法
        if not attr_name.startswith('__'):
            attr_value = getattr(msg, attr_name)
            print(f"Attribute: {attr_name}, Value: {attr_value}, Type: {type(attr_value)}")

def on_message(msg, chat):
    
    print("接受到消息")
    print(msg.content)
    # log(msg)
    # 检查消息是否@了当前用户
    current_nickname = wx.nickname
    # 方法1：直接检查content中是否包含@当前用户
    if f"@{current_nickname}\u2005" in msg.content:
        sender_name = msg.sender
        reply_content = f'你好 {sender_name}'
        msg.quote(reply_content)


# 添加监听，监听到的消息用on_message函数进行处理
# 监听群名为“测试群”
wx.AddListenChat(nickname="测试群", callback=on_message)

# 保持程序运行
wx.KeepRunning()