from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('YOUR_CHANNEL_ACCESS_TOKEN'))
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(channel_secret=os.getenv('YOUR_CHANNEL_SECRET'))
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
    try:
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
            reply_text = generate_response(msg)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
    except Exception as e:
        app.logger.error(f"handle_message error: {e}")

if __name__ == "__main__":
    app.run(debug=True)