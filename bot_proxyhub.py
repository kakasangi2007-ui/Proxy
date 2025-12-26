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
)

# فوتر پیام بدون اطلاعات اضافی
def footer(ts):
    return (
        "\n\n╔════════════════════╗\n"
        f"⏱ {ts}\n"
        "📡 @proxyhub_ir\n"
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

        # گرفتن متن خام پیام بدون تغییر
        text_div = msg.select_one("div.tgme_widget_message_text")
        if text_div:
            text = text_div.get_text(separator="\n").strip()
            messages.append((mid, text))
    return messages  # جدید → قدیم

# ساخت پیام‌ها با هدر و فوتر و تقسیم امن
def build_messages(texts):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    cur = HEADER

    for text in texts:
        piece = text + "\n\n"
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
    all_new_texts = []

    for src in SOURCES:
        last = state.get(src)
        msgs = fetch_channel(src)

        for mid, text in msgs:
            if last and mid == last:
                break
            all_new_texts.append(text)

        if msgs:
            state[src] = msgs[0][0]

    if not all_new_texts:
        print("📭 هیچ پیام جدیدی نیست")
        save_state(state)
        return

    messages = build_messages(all_new_texts)

    for m in messages:
        await bot.send_message(
            chat_id=TARGET_CHAT,
            text=m,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await asyncio.sleep(1)

    save_state(state)
    print(f"✅ ارسال شد | تعداد پیام‌ها: {len(all_new_texts)}")

# اجرا
if __name__ == "__main__":
    asyncio.run(main())
