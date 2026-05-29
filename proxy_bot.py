import os,re,json,asyncio,datetime,ipaddress
from urllib.parse import unquote
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import RetryAfter

BOT_TOKEN=os.getenv("BOT_TOKEN")
TARGET_CHAT=os.getenv("TARGET_CHAT")

SOURCE_URL="https://t.me/s/ProxysHUB"
STATE_FILE="state.json"

CHANNEL_USERNAME="@proxyhub_ir"

MAX_PROXIES=10
MAX_LEN=3500

HEADER="""
🔥 <b>پروکسی‌های جدید تلگرام</b> 🔥

┏━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 سریع و پایدار
┃ 🔒 رایگان
┃ ⚡ آماده اتصال
┗━━━━━━━━━━━━━━━━━━━━━━┛
"""

def footer():
    return f"""

╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 📅 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
┃ 📢 {CHANNEL_USERNAME}
┃ 💡 روی لینک بزنید
╰━━━━━━━━━━━━━━━━━━━━━━╯

#MTProto #Proxy
"""

def load_state():
    try:
        with open(STATE_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_post":0,"sent":[]}

def save_state(s):
    with open(STATE_FILE,"w",encoding="utf-8") as f:
        json.dump(s,f,ensure_ascii=False,indent=2)

def norm(x):
    return unquote(x.replace("&amp;","&").strip()) if x else None

def valid(proxy):
    try:
        if proxy.startswith(("tg://proxy?","https://t.me/proxy?")):
            return all(x in proxy for x in ["server=","port=","secret="])

        ip,port=proxy.split(":")[:2]
        ipaddress.ip_address(ip)
        return 1<=int(port)<=65535

    except:
        return False

async def fetch():

    async with aiohttp.ClientSession(
        headers={"User-Agent":"Mozilla/5.0"},
        timeout=aiohttp.ClientTimeout(total=20)
    ) as s:

        async with s.get(SOURCE_URL) as r:

            html=await r.text()

    soup=BeautifulSoup(html,"html.parser")

    data=[]

    for p in soup.select("div.tgme_widget_message"):

        pid=p.get("data-post")

        if not pid:
            continue

        try:
            pid=int(pid.split("/")[-1])
        except:
            continue

        proxies=set()

        for a in p.find_all("a",href=True):

            h=norm(a["href"])

            if h and ("proxy?" in h):
                proxies.add(h)

        html=str(p)

        rg=re.findall(
            r'(https:\/\/t\.me\/proxy\?[^\s"\']+|tg:\/\/proxy\?[^\s"\']+)',
            html
        )

        for x in rg:

            x=norm(x)

            if x:
                proxies.add(x)

        proxies=[x for x in proxies if valid(x)]

        data.append({
            "id":pid,
            "proxies":proxies
        })

    return data

def build(proxies):

    msgs=[]

    for i in range(0,len(proxies),5):

        text=HEADER

        for n,p in enumerate(proxies[i:i+5],start=i+1):

            text+=f"""
┣━━ 📍 <b>پروکسی {n}</b>
┃ 🔗 <code>{p}</code>
┃ ✅ فعال
┃
"""

        text+="╰━━━━━━━━━━━━━━━━━━━━━━╯"
        text+=footer()

        if len(text)<MAX_LEN:
            msgs.append(text)

    return msgs

async def send(bot,msgs):

    for i,m in enumerate(msgs,1):

        try:

            await bot.send_message(
                chat_id=TARGET_CHAT,
                text=m,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            print(f"✅ Sent {i}/{len(msgs)}")

            await asyncio.sleep(2)

        except RetryAfter as e:

            await asyncio.sleep(int(e.retry_after)+1)

        except Exception as e:

            print("❌",e)

async def main():

    if not BOT_TOKEN or not TARGET_CHAT:
        return print("❌ ENV missing")

    state=load_state()

    last=int(state.get("last_post",0))
    sent=set(state.get("sent",[]))

    print("🔍 Fetching...")

    try:
        posts=await fetch()
    except Exception as e:
        return print("❌ Fetch error:",e)

    if not posts:
        return print("📭 No posts")

    posts.sort(key=lambda x:x["id"])

    newest=last
    new=[]

    for post in posts:

        pid=post["id"]

        if pid>newest:
            newest=pid

        if pid<=last:
            continue

        for p in post["proxies"]:

            p=norm(p)

            if not p or p in sent or not valid(p):
                continue

            sent.add(p)
            new.append(p)

    if not new:

        print("📭 No new proxies")

        state["last_post"]=newest

        save_state(state)

        return

    new=new[-MAX_PROXIES:]

    print(f"📡 Found {len(new)} proxies")

    msgs=build(new)

    if not msgs:
        return print("❌ No valid messages")

    bot=Bot(BOT_TOKEN)

    await send(bot,msgs)

    state["last_post"]=newest
    state["sent"]=list(sent)[-5000:]

    save_state(state)

    print("🎉 Done")

if __name__=="__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("⛔ Stopped")

    except Exception as e:
        print("❌ Fatal:",e)
