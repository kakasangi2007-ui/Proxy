import os
import json
import re
import datetime
import asyncio
import aiohttp
import ipaddress

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import RetryAfter

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = os.getenv("TARGET_CHAT")

SOURCE_URL = "https://t.me/s/ProxysHUB"

STATE_FILE = "state.json"

CHANNEL_USERNAME = "@proxyhub_ir"

MAX_PROXIES_PER_RUN = 10
MAX_MESSAGE_LEN = 3000

# ==========================================

HEADER = """
🔥 <b>پروکسی‌های جدید تلگرام</b> 🔥

┏━━━━━━━━━━━━━━━━━━┓
┃ 🚀 سریع و پایدار
┃ 🔒 رایگان
┃ ⚡ آماده اتصال
┗━━━━━━━━━━━━━━━━━━┛

"""

def footer():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""

╭━━━━━━━━━━━━━━━━━━╮
┃ 📅 {now}
┃ 📢 {CHANNEL_USERNAME}
┃ 💡 روی لینک بزنید
╰━━━━━━━━━━━━━━━━━━╯

#MTProto #Proxy
"""

# ==========================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "last_post": 0,
        "sent": []
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

# ==========================================

def valid_ip_port(proxy):

    try:
        ip_port = proxy.split("@")[-1]

        if ":" not in ip_port:
            return True

        ip, port = ip_port.split(":")[:2]

        ipaddress.ip_address(ip)

        port = int(port)

        return 1 <= port <= 65535

    except:
        return False

# ==========================================

async def fetch_channel():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        async with session.get(SOURCE_URL, timeout=20) as r:

            html = await r.text()

    soup = BeautifulSoup(html, "html.parser")

    posts = soup.select("div.tgme_widget_message")

    results = []

    for post in posts:

        post_id = post.get("data-post")

        if not post_id:
            continue

        try:
            post_num = int(post_id.split("/")[-1])
        except:
            continue

        proxies = []

        # گرفتن لینک دکمه Connect
        buttons = post.select("a")

        for btn in buttons:

            href = btn.get("href", "")

            if not href:
                continue

            if (
                "t.me/proxy?" in href
                or "tg://proxy?" in href
            ):

                proxies.append(href)

        results.append({
            "id": post_num,
            "proxies": list(dict.fromkeys(proxies))
        })

    return results

# ==========================================

def format_proxy(proxy, index):

    return f"""
┣━━ 📍 <b>پروکسی {index}</b>
┃ 🔗 <code>{proxy}</code>
┃ ✅ فعال
┃
"""

# ==========================================

def build_messages(proxies):

    messages = []

    for i in range(0, len(proxies), 5):

        chunk = proxies[i:i+5]

        text = HEADER

        for idx, proxy in enumerate(chunk, start=i+1):

            text += format_proxy(proxy, idx)

        text += "╰━━━━━━━━━━━━━━━━━━╯"

        text += footer()

        if len(text) < MAX_MESSAGE_LEN:
            messages.append(text)

    return messages

# ==========================================

async def send_messages(bot, messages):

    for i, msg in enumerate(messages, 1):

        try:

            await bot.send_message(
                chat_id=TARGET_CHAT,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            print(f"✅ Sent {i}/{len(messages)}")

            await asyncio.sleep(2)

        except RetryAfter as e:

            print(f"⏳ FloodWait {e.retry_after}")

            await asyncio.sleep(e.retry_after)

        except Exception as e:

            print("❌", e)

# ==========================================

async def main():

    if not BOT_TOKEN or not TARGET_CHAT:

        print("❌ ENV not set")

        return

    bot = Bot(BOT_TOKEN)

    state = load_state()

    sent = set(state.get("sent", []))

    last_post = state.get("last_post", 0)

    print("🔍 Fetching...")

    posts = await fetch_channel()

    if not posts:

        print("❌ No posts")

        return

    new_proxies = []

    newest_post = last_post

    for post in posts:

        if post["id"] > newest_post:
            newest_post = post["id"]

        if post["id"] <= last_post:
            continue

        for proxy in post["proxies"]:

            if proxy in sent:
                continue

            if not valid_ip_port(proxy):
                continue

            sent.add(proxy)

            new_proxies.append(proxy)

    if not new_proxies:

        print("📭 No new proxies")

        state["last_post"] = newest_post
        save_state(state)

        return

    # فقط آخرین 10 تا
    new_proxies = new_proxies[-MAX_PROXIES_PER_RUN:]

    print(f"📡 {len(new_proxies)} proxies found")

    messages = build_messages(new_proxies)

    await send_messages(bot, messages)

    state["last_post"] = newest_post
    state["sent"] = list(sent)[-5000:]

    save_state(state)

    print("🎉 Done")

# ==========================================

if __name__ == "__main__":

    asyncio.run(main())
