from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import logging

app = Flask(__name__)

# ログを設定（エラーを詳しく表示）
logging.basicConfig(level=logging.INFO)

# 環境変数からAPIキーを取得
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_data(as_text=True)
        logging.info(f"Received Webhook: {body}")  # Webhookの内容をログに出力

        # LINEの署名検証（セキュリティ対策）
        signature = request.headers["X-Line-Signature"]
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            logging.error("Invalid signature. Check your channel secret.")
            return "Invalid signature", 400

        return "OK", 200
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")  # エラーをログに出力
        return "Internal Server Error", 500

# LINEメッセージを受け取ったら、ChatGPTに送る
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    try:
        # ChatGPT APIを使って応答を生成
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        reply_text = response["choices"][0]["message"]["content"]

        # LINEに返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    
    except Exception as e:
        logging.error(f"Error processing ChatGPT response: {str(e)}")  # エラーをログに出力

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

