import os, json, datetime, asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = os.getenv("TARGET_CHAT")
SOURCES = [
    "https://t.me/s/proxymtprotoir",
    "https://t.me/s/iMTProto",
    "https://t.me/s/TVProxy"
]
STATE_FILE = "last_proxy_messages.json"
MAX_LEN = 3500  # طول امن پیام

HEADER = (
    "╔════════════════════╗\n"
    "🧩 پروکسی هاب | Proxy Hub\n"
    "╚════════════════════╝\n\n"
)

def footer(ts):
    return (
        "\n\n╔════════════════════╗\n"
        f"⏱ {ts}\n"
        "📡 @proxyhub_ir\n"
        "╚════════════════════╝"
    )

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

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
                if any(proto in href.lower() for proto in ["vmess://", "vless://", "ss://", "trojan://", "hy2://", "http", "https"]):
                    proxies.append(f'<a href="{href}">{href}</a>')
            if proxies:
                messages.append((mid, proxies))
    return messages

def build_messages(all_proxies):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    cur_msg = HEADER
    cur_len = len(cur_msg)

    for proxies in all_proxies:
        line = " ".join(proxies) + " "
        if cur_len + len(line) + len(footer(now)) > MAX_LEN:
            # پیام فعلی رو ذخیره کن
            cur_msg = cur_msg.rstrip() + footer(now)
            messages.append(cur_msg)
            # شروع پیام جدید
            cur_msg = HEADER + line
            cur_len = len(cur_msg)
        else:
            cur_msg += line
            cur_len += len(line)

    if cur_msg.strip() != HEADER.strip():
        cur_msg = cur_msg.rstrip() + footer(now)
        messages.append(cur_msg)

    return messages

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

    messages = build_messages(all_new_proxies)
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

if __name__ == "__main__":
    asyncio.run(main())
