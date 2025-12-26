import requests
import re
import os
import json
import asyncio
import datetime
from telegram import Bot
from telegram.error import TelegramError

# ===================== تنظیمات =====================
SOURCE_CHANNELS = [
    "https://t.me/proxymtprotoir",
    "https://t.me/iMTProto",
    "https://t.me/TVProxy"
]

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DESTINATION_CHANNEL = "@proxyhub_ir"

# حداکثر طول پیام تلگرام
MAX_MESSAGE_LENGTH = 4000

# هدر و فوتر پیام
HEADER = "╔════════════════════╗\n🧩 پروکسی هاب | Proxy Hub\n╚════════════════════╝\n\n"
def footer(timestamp):
    return f"\n╔════════════════════╗\n⏱ {timestamp}\n📡 {DESTINATION_CHANNEL}\n╚════════════════════╝"

# ===================== توابع =====================
def extract_proxies(html_content):
    """لینک‌های پروکسی را از HTML کانال استخراج می‌کند"""
    proxies = []
    # لینک‌های تلگرام با فرمت t.me/proxy?server=...
    link_pattern = r'https://t\.me/proxy\?server=[^\s"\']+'
    matches = re.findall(link_pattern, html_content)
    for link in matches:
        proxies.append(link.strip())
    return proxies

def split_messages(proxies):
    """لینک‌ها را در پیام‌های مختلف با طول مجاز تقسیم می‌کند"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []
    current_text = HEADER

    for link in proxies:
        link_html = f'<a href="{link}">{link}</a>'
        # +1 برای اسپیس
        if len(current_text) + len(link_html) + 1 + len(footer(now)) > MAX_MESSAGE_LENGTH:
            current_text += footer(now)
            messages.append(current_text)
            current_text = HEADER + link_html + " "
        else:
            current_text += link_html + " "

    if current_text.strip() != HEADER.strip():
        current_text += footer(now)
        messages.append(current_text)

    return messages

async def fetch_and_send(bot, url):
    """یک کانال را بررسی کرده و پروکسی‌ها را ارسال می‌کند"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"❌ خطا در دریافت {url} (HTTP {resp.status_code})")
            return 0

        proxies = extract_proxies(resp.text)
        if not proxies:
            print(f"📭 پروکسی جدیدی یافت نشد در {url}")
            return 0

        messages = split_messages(proxies)
        for msg in messages:
            try:
                await bot.send_message(
                    chat_id=DESTINATION_CHANNEL,
                    text=msg,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                await asyncio.sleep(1)
            except TelegramError as e:
                print(f"❌ خطا در ارسال پیام: {e}")
        print(f"✅ {len(proxies)} پروکسی از {url} ارسال شد")
        return len(proxies)
    except Exception as e:
        print(f"❌ خطا در بررسی {url}: {e}")
        return 0

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN تنظیم نشده!")
        return

    bot = Bot(token=BOT_TOKEN)
    total = 0
    for url in SOURCE_CHANNELS:
        count = await fetch_and_send(bot, url)
        total += count
        await asyncio.sleep(2)

    print(f"\n📊 مجموع پروکسی‌های ارسال شده: {total}")

if __name__ == "__main__":
    asyncio.run(main())
