from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('YOUR_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('YOUR_CHANNEL_SECRET'))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_response(prompt, role="user"):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": role, "content": prompt}]
    )
    return response.choices[0].message.content

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.lower()
    if msg.startswith('/echo '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg[6:])
        )
    elif msg.startswith('/g '):
        response = generate_response(msg[3:])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    elif msg.startswith('/t '):
        response = generate_response("請幫我翻譯成正體中文：" + msg[3:])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    elif msg.startswith('/e '):
        response = generate_response("請幫我翻譯成英文：" + msg[3:])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    else:
        # 預設回應
        reply_text = generate_response(msg)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

if __name__ == "__main__":
    app.run(debug=True)