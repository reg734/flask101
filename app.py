from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest
from linebot.v3.messaging.models import TextSendMessage
import os
import json
import openai
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

app = Flask(__name__)

# 設定 LINE 與 OpenAI
configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(configuration)
openai.api_key = os.getenv("OPENAI_API_KEY")

# 健康檢查 route
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
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"[OpenAI 錯誤] {e}")
        return "⚠️ OpenAI 回覆失敗，請稍後再試。"

# Webhook callback
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print(f"[Webhook 收到] {body}")

    try:
        events = json.loads(body).get("events", [])
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_text = event["message"]["text"].strip()
                reply_token = event["replyToken"]
                print(f"[收到訊息] {user_text}")

                # 回覆文字處理
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

                # 發送回覆（v3 寫法）
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextSendMessage(text=reply_text)]
                    )
                )
    except Exception as e:
        print(f"[處理 callback 錯誤] {e}")
        abort(500)

    return "OK"

if __name__ == "__main__":
    app.run(debug=True)
