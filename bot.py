import os, json, re, asyncio, datetime
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = "@proxyhub_ir"

SOURCES = [
    "https://t.me/s/Proxymelimon",
    "https://t.me/s/MaKVaslim",
    "https://t.me/s/BestProxyTel1",
    "https://t.me/s/iMTProto",
    "https://t.me/s/iRoProxy",
]

STATE_FILE = "state.json"

PROXIES_PER_POST = 4
MAX_POSTS = 3
# =========================================


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def fetch_channel(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = soup.select("div.tgme_widget_message")
    result = []

    for p in posts:
        mid = p.get("data-post")
        text = p.get_text("\n", strip=True)
        if mid:
            result.append((mid, text))

    return result


def extract_proxies(text):
    pattern = r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+|ssr://[^\s]+|tg://proxy\?[^\s]+)'
    return re.findall(pattern, text)


# ---------- UI ----------
def header():
    return (
        "╔════════════════════╗\n"
        "🚀 <b>پروکسی‌های آماده اتصال</b>\n"
        "╚════════════════════╝\n\n"
        "🟢 تست‌شده • پایدار\n"
        "👆 روی کارت‌ها بزن و وصل شو\n\n"
    )

def proxy_card(proxy):
    return f"""
<blockquote>
<tg-spoiler>
🔗 <b>پروکسی فعال</b>

🚀 اتصال سریع  
❌ بدون نیاز به کپی

👉 <a href="{proxy}">وصل شو</a>
</tg-spoiler>
</blockquote>
"""

def footer():
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        "\n━━━━━━━━━━━━\n"
        "⚡ <b>ProxyHub IR</b>\n"
        "@proxyhub_ir\n"
        f"⏱ {t}"
    )


async def main():
    bot = Bot(BOT_TOKEN)
    state = load_state()
    all_new = []

    for src in SOURCES:
        last = state.get(src)
        posts = fetch_channel(src)

        for mid, text in posts:
            if last and mid <= last:
                break
            all_new.extend(extract_proxies(text))

        if posts:
            state[src] = posts[0][0]

    if not all_new:
        print("📭 پروکسی جدیدی نبود")
        save_state(state)
        return

    sent = 0
    for i in range(0, len(all_new), PROXIES_PER_POST):
        if sent >= MAX_POSTS:
            break

        batch = all_new[i:i + PROXIES_PER_POST]
        msg = header()

        for p in batch:
            msg += proxy_card(p)

        msg += footer()

        await bot.send_message(
            chat_id=TARGET_CHAT,
            text=msg,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        sent += 1
        await asyncio.sleep(1)

    save_state(state)
    print(f"✅ ارسال شد | پست‌ها: {sent}")


if __name__ == "__main__":
    asyncio.run(main())
