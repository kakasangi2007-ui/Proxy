import os, json, datetime, asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ======== تنظیمات =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = os.getenv("TARGET_CHAT")  # @proxyhub_ir
SOURCES = [
    "https://t.me/s/proxymtprotoir",
    "https://t.me/s/iMTProto",
    "https://t.me/s/TVProxy"
]
STATE_FILE = "last_proxy_messages.json"

MAX_MESSAGE_LENGTH = 3500  # طول امن برای هر پیام

# ======== هدر و فوتر =========
HEADER = "╔════════════════════╗\n🧩 پروکسی هاب | Proxy Hub\n╚════════════════════╝\n\n"
def footer(ts):
    return f"\n\n╔════════════════════╗\n⏱ {ts}\n📡 @proxyhub_ir\n╚════════════════════╝"

# ======== مدیریت تاریخچه پیام‌ها =========
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

# ======== استخراج پروکسی‌ها از کانال =========
def fetch_channel(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    messages = []
    for msg in soup.select("div.tgme_widget_message"):
        mid = msg.get("data-post")
        if not mid:
            continue
        text_div = msg.select_one("div.tgme_widget_message_text")
        if text_div:
            links = text_div.find_all("a", href=True)
            proxies = []
            for l in links:
                href = l['href'].strip()
                # فقط پروکسی‌ها یا لینک‌های subscribe
                if any(proto in href.lower() for proto in ["vmess://", "vless://", "ss://", "trojan://", "hy2://", "http", "https"]):
                    proxies.append(f'<a href="{href}">{href}</a>')
            if proxies:
                messages.append((mid, proxies))
    return messages

# ======== ساخت پیام‌ها با تقسیم طول امن =========
def build_messages_safe_by_length(all_proxies):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    current_text = HEADER
    for proxies in all_proxies:
        for link in proxies:
            if len(current_text) + len(link) + 1 + len(footer(now)) > MAX_MESSAGE_LENGTH:
                current_text += footer(now)
                messages.append(current_text)
                current_text = HEADER + link + " "
            else:
                current_text += link + " "
    if current_text.strip() != HEADER.strip():
        current_text += footer(now)
        messages.append(current_text)
    return messages

# ======== تابع اصلی =========
async def main():
    bot = Bot(BOT_TOKEN)
    state = load_state()
    all_new_proxies = []

    for src in SOURCES:
        last_id = state.get(src)
        msgs = fetch_channel(src)
        for mid, proxies in msgs:
            if last_id and mid == last_id:
                break
            all_new_proxies.append(proxies)
        if msgs:
            state[src] = msgs[0][0]

    if not all_new_proxies:
        print("📭 هیچ پیام جدیدی نیست")
        save_state(state)
        return

    messages = build_messages_safe_by_length(all_new_proxies)
    for m in messages:
        await bot.send_message(
            chat_id=TARGET_CHAT,
            text=m,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await asyncio.sleep(1)

    save_state(state)
    print(f"✅ ارسال شد | تعداد پیام‌ها: {len(messages)}")

# ======== اجرا =========
if __name__ == "__main__":
    asyncio.run(main())
