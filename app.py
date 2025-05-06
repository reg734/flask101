from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import openai
from dotenv import load_dotenv
import json
from linebot.models import *

# 載入 .env 環境變數
load_dotenv()

# 初始化 Flask app
app = Flask(__name__)

# 設定 LINE Messaging API 與 OpenAI
configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(channel_secret=os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# 方便 render 檢查用的首頁
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

# ChatGPT 回覆邏輯
def generate_response(prompt, role="user"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": role, "content": prompt}]
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"[OpenAI 錯誤] {e}")
        return "⚠️ 無法從 ChatGPT 取得回覆，請稍後再試。"

# LINE Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print(f"[Webhook 收到] {body}")

    try:
        events = json.loads(body)["events"]
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_text = event["message"]["text"]
                reply_token = event["replyToken"]
                print(f"[收到訊息] {user_text}")

                if user_text.lower().startswith("/echo "):
                    reply_text = user_text[6:]
                elif user_text.lower().startswith("/g "):
                    reply_text = generate_response(user_text[3:])
                elif user_text.lower().startswith("/t "):
                    reply_text = generate_response("請翻譯成正體中文：" + user_text[3:])
                elif user_text.lower().startswith("/e "):
                    reply_text = generate_response("請翻譯成英文：" + user_text[3:])
                else:
                    reply_text = generate_response(user_text)

                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text=reply_text)
                )
    except Exception as e:
        print(f"[處理 callback 錯誤] {e}")
        abort(500)

    return 'OK'

# 訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        msg = event.message.text.strip()
        print(f"[收到訊息] {msg}")

        # /echo 回覆
        if msg.lower().startswith('/echo '):
            reply = msg[6:]

        # /g 啟用 ChatGPT
        elif msg.lower().startswith('/g '):
            reply = generate_response(msg[3:])

        # 翻譯成繁中
        elif msg.lower().startswith('/t '):
            reply = generate_response("請翻譯成正體中文：" + msg[3:])

        # 翻譯成英文
        elif msg.lower().startswith('/e '):
            reply = generate_response("請翻譯成英文：" + msg[3:])

        # 默認直接丟 ChatGPT
        else:
            reply = generate_response(msg)

        # 回傳給用戶
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

    except Exception as e:
        print(f"[處理訊息錯誤] {e}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ 發生錯誤，請稍後再試。")
            )
        except:
            pass  # reply_token 可能已過期，忽略


if __name__ == "__main__":
    app.run(debug=True)
