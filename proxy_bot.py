import os, json, re, datetime, asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = os.getenv("TARGET_CHAT")  # میتونه @proxyhub_ir باشه

SOURCE_URL = "https://t.me/s/ProxysHUB"
STATE_FILE = "last_messages.json"
MAX_LEN = 3800
MAX_PROXIES_PER_RUN = 10  # حداکثر 10 پروکسی

CHANNEL_USERNAME = "@proxyhub_ir"
# ===========================================

# قالب خفن
HEADER = (
    "🔥 **پروکسی‌های تلگرام - تازه‌ترین‌ها** 🔥\n\n"
    "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
    "┃ **🚀 آماده استفاده در تلگرام**\n"
    "┃ **⚡ سرعت بالا | پایدار**\n"
    "┃ **🔒 کاملاً رایگان**\n"
    "┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    "📡 **پروکسی‌های امروز:**\n\n"
)

def footer(ts: str) -> str:
    return (
        f"\n\n"
        f"╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃ 📅 {ts}\n"
        f"┃ 📢 {CHANNEL_USERNAME}\n"
        f"┃ 💡 **نصب**: کافیست روی لینک کلیک کنید\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"#پروکسی_تلگرام #MTProto #رایگان"
    )

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def fetch_channel():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(SOURCE_URL, timeout=20, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.tgme_widget_message")

        messages = []
        for p in posts:
            mid = p.get("data-post")
            if not mid:
                continue
            text = p.get_text("\n", strip=True)
            messages.append((mid, text))

        return messages
    except Exception as e:
        print(f"Error: {e}")
        return []

def extract_proxies(text):
    """استخراج پروکسی‌های MTProto و سایر فرمت‌ها"""
    mtproto_pattern = r'https?://t\.me/proxy\?[^\s<>"\']+'
    mtproto_proxies = re.findall(mtproto_pattern, text)
    
    other_pattern = r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]+'
    other_proxies = re.findall(other_pattern, text)
    
    all_proxies = mtproto_proxies + other_proxies
    return list(dict.fromkeys(all_proxies))

def is_valid_proxy(proxy):
    if not proxy:
        return False
    
    if proxy.startswith('https://t.me/proxy?'):
        return 'server=' in proxy and 'port=' in proxy
    
    if re.match(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]+', proxy):
        try:
            ip, port = proxy.split(':')
            parts = list(map(int, ip.split('.')))
            port = int(port)
            if all(0 <= p <= 255 for p in parts) and 1 <= port <= 65535:
                return True
        except:
            pass
    return False

def format_proxy(proxy, index):
    """فرمت‌دهی خفن برای هر پروکسی"""
    if proxy.startswith('https://t.me/proxy?'):
        return f"┣━━ 📍 **پروکسی {index}**\n┃   🔗 `{proxy}`\n┃   ✅ وضعیت: فعال\n"
    else:
        return f"┣━━ 📍 **پروکسی {index}**\n┃   🔗 `{proxy}`\n┃   📝 نوع: SOCKS/HTTP\n"

def build_messages(proxies):
    """ساخت پیام‌های نهایی با قالب جدید"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    
    for i in range(0, len(proxies), 5):  # هر پیام حداکثر 5 پروکسی
        msg = HEADER
        for j, proxy in enumerate(proxies[i:i+5], start=i+1):
            msg += format_proxy(proxy, j)
            msg += "┃\n"
        
        msg += "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n"
        msg += footer(now)
        
        if len(msg) > MAX_LEN:
            for proxy in proxies[i:i+5]:
                single_msg = HEADER + format_proxy(proxy, 1) + "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n" + footer(now)
                messages.append(single_msg)
        else:
            messages.append(msg)
    
    return messages

async def main():
    if not BOT_TOKEN or not TARGET_CHAT:
        print("BOT_TOKEN or TARGET_CHAT not set!")
        return

    bot = Bot(BOT_TOKEN)
    state = load_state()
    all_new_proxies = []
    last_id = state.get("last_id")

    print("🔍 Fetching from ProxysHUB...")
    posts = fetch_channel()

    if not posts:
        print("❌ No posts found")
        return

    # جمع‌آوری همه پروکسی‌های جدید
    for mid, text in posts:
        if last_id and mid <= last_id:
            break
        
        proxies = extract_proxies(text)
        for proxy in proxies:
            if is_valid_proxy(proxy) and proxy not in all_new_proxies:
                all_new_proxies.append(proxy)

    if posts:
        state["last_id"] = posts[0][0]

    if not all_new_proxies:
        print("📭 No new proxies found")
        save_state(state)
        return

    # گرفتن آخرین 10 پروکسی (جدیدترین‌ها)
    original_count = len(all_new_proxies)
    if len(all_new_proxies) > MAX_PROXIES_PER_RUN:
        all_new_proxies = all_new_proxies[-MAX_PROXIES_PER_RUN:]  # آخرین 10 تا
        print(f"📊 Found {original_count} total, sending last {len(all_new_proxies)} proxies")
    else:
        print(f"📊 Found {len(all_new_proxies)} new proxies")

    messages = build_messages(all_new_proxies)
    print(f"📨 Sending {len(messages)} messages")

    for i, msg in enumerate(messages, 1):
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False
            )
            print(f"✅ Sent message {i}/{len(messages)}")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ Failed: {e}")

    save_state(state)
    print("🎉 Job completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
