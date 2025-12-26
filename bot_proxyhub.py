import os, json, datetime, asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # توکن بات
TARGET_CHAT = os.getenv("TARGET_CHAT")  # کانال مقصد
SOURCES = [
    "https://t.me/s/proxymtprotoir",
    "https://t.me/s/iMTProto",
    "https://t.me/s/TVProxy"
]
STATE_FILE = "last_proxy_messages.json"
MAX_LEN = 3800  # حداکثر طول پیام
# ==========================================

# هدر پیام
HEADER = (
    "╔════════════════════╗\n"
    "🧩 پروکسی هاب | Proxy Hub\n"
    "╚════════════════════╝\n\n"
    "⚡ پروکسی‌های فعال و سریع\n"
    "📱 آیفون | اندروید | دسکتاپ\n\n"
)

# فوتر پیام
def footer(ts):
    return (
        "\n\n╔════════════════════╗\n"
        f"⏱ {ts}\n"
        "📡 @proxyhub_ir\n"
        "🌐 configfree.github.io\n"
        "╚════════════════════╝"
    )

# بارگذاری وضعیت پیام‌ها
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ذخیره وضعیت پیام‌ها
def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

# دریافت پیام‌های کانال منبع
def fetch_channel(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    messages = []
    for msg in soup.select("div.tgme_widget_message"):
        mid = msg.get("data-post")
        if not mid:
            continue

        links = []
        for a in msg.select("a[href]"):
            href = a["href"]
            if "proxy?server=" in href:
                links.append(href)

        messages.append((mid, links))
    return messages  # جدید → قدیم

# ساخت پیام‌ها با هدر و فوتر و تقسیم امن
def build_messages(links):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    cur = HEADER

    for link in links:
        piece = link + "\n"
        if len(cur) + len(piece) + len(footer(now)) > MAX_LEN:
            cur = cur.rstrip("\n") + footer(now)
            messages.append(cur)
            cur = HEADER + piece
        else:
            cur += piece

    if cur.strip() != HEADER.strip():
        cur = cur.rstrip("\n") + footer(now)
        messages.append(cur)

    return messages

# تابع اصلی
async def main():
    bot = Bot(BOT_TOKEN)
    state = load_state()
    all_new_links = []

    for src in SOURCES:
        last = state.get(src)
        msgs = fetch_channel(src)

        for mid, links in msgs:
            if last and mid == last:
                break
            all_new_links.extend(links)

        if msgs:
            state[src] = msgs[0][0]

    if not all_new_links:
        print("📭 پروکسی جدیدی نیست")
        save_state(state)
        return

    messages = build_messages(all_new_links)

    for m in messages:
        await bot.send_message(
            chat_id=TARGET_CHAT,
            text=m,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await asyncio.sleep(1)

    save_state(state)
    print(f"✅ ارسال شد | تعداد پروکسی: {len(all_new_links)}")

# اجرا
if __name__ == "__main__":
    asyncio.run(main())
