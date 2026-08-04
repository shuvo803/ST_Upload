import os, time, re
from typing import List
id_pattern = re.compile(r'^.\d+$')

class Config(object):
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    DATABASE_NAME = os.environ.get("DATABASE_NAME","shuvobot")     
    DATABASE_URL = os.environ.get("DATABASE_URL","")
    PICS = (os.environ.get("PICS", "https://i.ibb.co.com/WW33G4VH/20260804-054313.jpg")).split()
    ADMIN = int(os.environ.get("ADMIN", "0"))
    IS_FSUB = os.environ.get("IS_FSUB", "False").lower() == "true"  # Set "True" For Enable Force Subscribe
    AUTH_CHANNELS = list(map(int, os.environ.get("AUTH_CHANNELS", "").split())) if os.environ.get("AUTH_CHANNELS") else [] # Add Multiple channel ids
    AUTH_REQ_CHANNELS = list(map(int, os.environ.get("AUTH_REQ_CHANNELS", "").split())) if os.environ.get("AUTH_REQ_CHANNELS") else [] # Add Multiple channel ids
    FSUB_EXPIRE = int(os.environ.get("FSUB_EXPIRE", 2))  # minutes, 0 = no expiry
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
    BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", "0"))
    # Render Web Service needs an open $PORT, so keep this True when deploying on Render.
    WEBHOOK = os.environ.get("WEBHOOK", "True").lower() == "true"
    PORT = int(os.environ.get("PORT", 8000))
    BOT_UPTIME = time.time()


class Txt(object):
    START_TXT = """ʜᴇʏ {}!✨

🫧 <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʀᴇɴᴀᴍᴇ & ᴜʀʟ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ!
ᴡʜɪᴄʜ ᴄᴀɴ ᴍᴀɴᴜᴀʟʟʏ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ғɪʟᴇs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴀɴᴅ ᴀʟsᴏ ᴄᴀɴ sᴇᴛ ᴘʀᴇғɪx ᴀɴᴅ sᴜғғɪx ᴏɴ ʏᴏᴜʀ ғɪʟᴇs.⚡️</b>

<blockquote><b>✨ <b>ᴛʜɪs ʙᴏᴛ ɪs ᴅᴇᴘʟᴏʏᴇᴅ ʙʏ <a href='https://t.me/kog_shuvo'>[Sʜᴜꪜᴏ]</a></b> </blockquote>
──────────────────
๏ <b>ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴏᴡ ᴛᴏ ᴜsᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs.</b>"""

    ABOUT_TXT = """‣ 𝖬𝗒 𝖭𝖺𝗆𝖾 : <a href='https://t.me/URL_UPLOADER_TS_bot'>sᴛ ʀᴇɴᴀᴍᴇ ʙᴏᴛ</a>
‣ 𝖫𝗂𝖻𝗋𝖺𝗋𝗒 : <a href='https://docs.pyrogram.org/'>𝖯𝗒𝗋𝗈𝗀𝗋𝖺𝗆</a>
‣ 𝖣𝖺𝗍𝖺𝖻𝖺𝗌𝖾 : <a href='https://www.mongodb.com/'>𝖬𝗈𝗇𝗀𝗈𝖣𝖡</a>
‣ 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 : <a href='https://www.python.org/download/releases/3.0/'>𝖯𝗒𝗍𝗁𝗈𝗇 𝟹</a>
‣ 𝖡𝗈𝗍 𝖲𝖾𝗋𝗏𝖾𝗋 : <a href='https://www.render.com/'>ʀᴇɴᴅᴇʀ</a>
‣ 𝖢𝗋𝖾𝖺𝗍𝖾𝖽 𝖡𝗒 : <a href='https://telegram.me/kog_shuvo'>[Sʜᴜꪜᴏ]</a>"""

    HELP_TXT = """<b>𝖲ʜᴜᴠᴏ 𝖱ᴇɴᴀᴍᴇ 𝖡ᴏᴛ Is A Vᴇʀʏ Hᴀɴᴅʏ Aɴᴅ Hᴇʟᴘғᴜʟ Bᴏᴛ Tʜᴀᴛ Hᴇʟᴘs Yᴏᴜ Rᴇɴᴀᴍᴇ Aɴᴅ Mᴀɴᴀɢᴇ Yᴏᴜʀ Fɪʟᴇs Eғғᴏʀᴛʟᴇssʟʏ.</b>

<u><b>𝖨𝗆𝗉𝗈𝗋𝗍𝖺𝗇𝗍 𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌 :</b></u>
↬ 𝖢𝖺𝗇 𝗋𝖾𝗇𝖺𝗆𝖾 𝖺𝗇𝗒 𝖿𝗂𝗅𝖾𝗌 (𝖽𝗈𝖼𝗎𝗆𝖾𝗇𝗍/𝗏𝗂𝖽𝖾𝗈).
↬ 𝖢𝖺𝗇 𝖽𝗈𝗐𝗇𝗅𝗈𝖺𝖽 & 𝗋𝖾𝗇𝖺𝗆𝖾 𝖽𝗂𝗋𝖾𝖼𝗍𝗅𝗒 𝖿𝗋𝗈𝗆 𝖺 𝖴𝖱𝖫.
↬ 𝖢𝖺𝗇 𝗆𝖺𝗇𝖺𝗀𝖾 𝖼𝗎𝗌𝗍𝗈𝗆 𝗆𝖾𝗍𝖺𝖽𝖺𝗍𝖺.
↬ 𝖢𝖺𝗇 𝖾𝗆𝖻𝖾𝖽 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌 (.𝗌𝗋𝗍) 𝗂𝗇𝗍𝗈 𝗒𝗈𝗎𝗋 𝗏𝗂𝖽𝖾𝗈𝗌.
↬ 𝖴𝗉𝗅𝗈𝖺𝖽 𝗂𝗇 𝖽𝖾𝗌𝗂𝗋𝖾𝖽 𝗆𝖾𝖽𝗂𝖺 𝗍𝗒𝗉𝖾 (𝖣𝗈𝖼𝗎𝗆𝖾𝗇𝗍/𝖵𝗂𝖽𝖾𝗈).
↬ 𝖢𝖺𝗇 𝗌𝖾𝗍 𝖼𝗎𝗌𝗍𝗈𝗆 𝗉𝗋𝖾𝖿𝗂𝗑, 𝗌𝗎𝖿𝖿𝗂𝗑, 𝖼𝖺𝗉𝗍𝗂𝗈𝗇 & 𝗍𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅.
↬ 𝖱𝖾𝗇𝖺𝗆𝖾𝗌 𝖿𝗂𝗅𝖾𝗌 𝗏𝖾𝗋𝗒 𝗊𝗎𝗂𝖼𝗄𝗅𝗒.

➻ 𝖢𝗅𝗂𝖼𝗄 𝖮𝗇 𝖳𝗁𝖾 𝖡𝗎𝗍𝗍𝗈𝗇𝗌 𝖦𝗂𝗏𝖾𝗇 𝖡𝖾𝗅𝗈𝗐 𝖥𝗈𝗋 𝖦𝖾𝗍𝗍𝗂𝗇𝗀 𝖬𝗈𝗋𝖾 𝖨𝗇𝖿𝗈."""

    THUMBNAIL_TXT = """<blockquote>🖼 𝖳𝗈 𝖲𝖾𝗍 𝖢𝗎𝗌𝗍𝗈𝗆 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅</blockquote>

➲ 𝖲𝖾𝗇𝖽 𝖠𝗇𝗒 𝖯𝗁𝗈𝗍𝗈 𝖳𝗈 𝖠𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒 𝖲𝖾𝗍 𝖨𝗍 𝖠𝗌 𝖠 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅.  
➲ /delthumb: 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌 𝖢𝗈𝗆𝗆𝖺𝗇𝖽 𝖳𝗈 𝖣𝖾𝗅𝖾𝗍𝖾 𝖸𝗈𝗎𝗋 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅.  
➲ /viewthumb: 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌 𝖢𝗈𝗆𝗆𝖺𝗇𝖽 𝖳𝗈 𝖵𝗂𝖾𝗐 𝖸𝗈𝗎𝗋 𝖢𝗎𝗋𝗋𝖾𝗇𝗍 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅.

<b>𝖭𝗈𝗍𝖾 :</b> 𝖨𝖿 𝖭𝗈 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅 𝖲𝖺𝗏𝖾𝖽 𝖨𝗇 𝖡𝗈𝗍 𝖳𝗁𝖾𝗇, 𝖨𝗍 𝖶𝗂𝗅𝗅 𝖴𝗌𝖾 𝖳𝗁𝗎𝗆𝖻𝗇𝖺𝗂𝗅 𝖮𝖿 𝖳𝗁𝖾 𝖮𝗋𝗂𝗀𝗂𝗇𝖺𝗅 𝖥𝗂𝗅𝖾 𝖳𝗈 𝖲𝖾𝗍 𝖨𝗇 𝖱𝖾𝗇𝖺𝗆𝖾𝖽 𝖥𝗂𝗅𝖾."""

    CAPTION_TXT = """<blockquote>📝 𝖳𝗈 𝖲𝖾𝗍 𝖢𝗎𝗌𝗍𝗈𝗆 𝖢𝖺𝗉𝗍𝗂𝗈𝗇 𝖠𝗇𝖽 𝖬𝖾𝖽𝗂𝖺 𝖳𝗒𝗉𝖾</blockquote>

<b>𝖵𝖺𝗋𝗂𝖺𝖻𝗅𝖾𝗌 :</b>         
𝖲𝗂𝗓𝖾: {filesize}  
𝖣𝗎𝗋𝖺𝗍𝗂𝗈𝗇: {duration}  
𝖥𝗂𝗅𝖾𝗇𝖺𝗆𝖾: {filename}

➲ /setcaption: 𝖳𝗈 𝖲𝖾𝗍 𝖠 𝖢𝗎𝗌𝗍𝗈𝗆 𝖢𝖺𝗉𝗍𝗂𝗈𝗇.  
➲ /seecaption: 𝖳𝗈 𝖵𝗂𝖾𝗐 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖢𝖺𝗉𝗍𝗂𝗈𝗇.  
➲ /delcaption: 𝖳𝗈 𝖣𝖾𝗅𝖾𝗍𝖾 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖢𝖺𝗉𝗍𝗂𝗈𝗇.

» 𝖤𝗑: /setcaption 𝖥𝗂𝗅𝖾 𝖭𝖺𝗆𝖾: {filename}"""

    PREFIX = """<blockquote>📜 𝖳𝗈 𝖲𝖾𝗍 𝖢𝗎𝗌𝗍𝗈𝗆 𝖯𝗋𝖾𝖿𝗂𝗑</blockquote>

➲ /setprefix: 𝖳𝗈 𝖲𝖾𝗍 𝖠 𝖢𝗎𝗌𝗍𝗈𝗆 𝖯𝗋𝖾𝖿𝗂𝗑.  
➲ /seeprefix: 𝖳𝗈 𝖵𝗂𝖾𝗐 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖯𝗋𝖾𝖿𝗂𝗑.  
➲ /delprefix: 𝖳𝗈 𝖣𝖾𝗅𝖾𝗍𝖾 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖯𝗋𝖾𝖿𝗂𝗑.

» 𝖤𝗑: `/setprefix @Sʜᴜꪜᴏ`"""

    SUFFIX = """<blockquote>📜 𝖳𝗈 𝖲𝖾𝗍 𝖢𝗎𝗌𝗍𝗈𝗆 𝖲𝗎𝖿𝖿𝗂𝗑</blockquote>

➲ /setsuffix: 𝖳𝗈 𝖲𝖾𝗍 𝖠 𝖢𝗎𝗌𝗍𝗈𝗆 𝖲𝗎𝖿𝖿𝗂𝗑.  
➲ /seesuffix: 𝖳𝗈 𝖵𝗂𝖾𝗐 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖲𝗎𝖿𝖿𝗂𝗑.  
➲ /delsuffix: 𝖳𝗈 𝖣𝖾𝗅𝖾𝗍𝖾 𝖸𝗈𝗎𝗋 𝖢𝗎𝗌𝗍𝗈𝗆 𝖲𝗎𝖿𝖿𝗂𝗑.

» 𝖤𝗑: `/setsuffix @Sʜᴜꪜᴏ`"""

    SUBTITLE_TXT = """<blockquote>🎬 𝖳𝗈 𝖤𝗆𝖻𝖾𝖽 𝖲𝗎𝖻𝗍𝗂𝗍𝗅𝖾</blockquote>

➲ 𝖳𝖺𝗉 "𝖲𝖾𝗍 𝖭𝖾𝗐 𝖲𝗎𝖻𝗍𝗂𝗍𝗅𝖾" 𝖠𝗇𝖽 𝖲𝖾𝗇𝖽 𝖠𝗇 .𝗌𝗋𝗍 𝖥𝗂𝗅𝖾 𝖳𝗈 𝖲𝖺𝗏𝖾 𝖨𝗍.  
➲ /subtitle: 𝖳𝗈 𝖵𝗂𝖾𝗐/𝖳𝗈𝗀𝗀𝗅𝖾 𝖸𝗈𝗎𝗋 𝖲𝗎𝖻𝗍𝗂𝗍𝗅𝖾 𝖲𝖾𝗍𝗍𝗂𝗇𝗀𝗌.

<b>𝖭𝗈𝗍𝖾 :</b> 𝖮𝗇𝗅𝗒 𝖠𝗉𝗉𝗅𝗂𝖾𝗌 𝖶𝗁𝖾𝗇 𝖸𝗈𝗎 𝖢𝗁𝗈𝗈𝗌𝖾 "𝖵𝗂𝖽𝖾𝗈" 𝖠𝗌 𝖳𝗁𝖾 𝖮𝗎𝗍𝗉𝗎𝗍 𝖳𝗒𝗉𝖾 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗇𝖺𝗆𝗂𝗇𝗀."""

    PROGRESS_BAR = """\n
<b>😶‍🌫 𝖲𝗂𝗓𝖾 :</b> {1} | {2}
<b>⏳️ 𝖣𝗈𝗇𝖾 :</b> {0}%
<b>🚀 𝖲𝗉𝖾𝖾𝖽 :</b> {3}/s
<b>⏰️ 𝖤𝖳𝖠 :</b> {4}
"""

    DONATE_TXT = """<blockquote>❤️‍🔥 𝐓𝐡𝐚𝐧𝐤𝐬 𝐟𝐨𝐫 𝐬𝐡𝐨𝐰𝐢𝐧𝐠 𝐢𝐧𝐭𝐞𝐫𝐞𝐬𝐭 𝐢𝐧 𝐃𝐨𝐧𝐚𝐭𝐢𝐨𝐧</blockquote>

<b><i>💞  ɪꜰ ʏᴏᴜ ʟɪᴋᴇ ᴏᴜʀ ʙᴏᴛ ꜰᴇᴇʟ ꜰʀᴇᴇ ᴛᴏ ᴅᴏɴᴀᴛᴇ ᴀɴʏ ᴀᴍᴏᴜɴᴛ ৳𝟷𝟶, ৳𝟸𝟶, ৳𝟻𝟶, ৳𝟷𝟶𝟶, ᴇᴛᴄ.</i></b>

❣️ 𝐷𝑜𝑛𝑎𝑡𝑖𝑜𝑛𝑠 𝑎𝑟𝑒 𝑟𝑒𝑎𝑙𝑙𝑦 𝑎𝑝𝑝𝑟𝑒𝑐𝑖𝑎𝑡𝑒𝑑 𝑖𝑡 ℎ𝑒𝑙𝑝𝑠 𝑖𝑛 𝑏𝑜𝑡 𝑑𝑒𝑣𝑒𝑙𝑜𝑝𝑚𝑒𝑛𝑡

💗 𝐁𝐤𝐚𝐬𝐡 (𝑃𝑒𝑟𝑠𝑜𝑛𝑎𝑙) : `01894189895`

💚 𝐍𝐚𝐠𝐚𝐝 (𝑃𝑒𝑟𝑠𝑜𝑛𝑎𝑙) : `01894189895`
"""

    SEND_METADATA = """<blockquote>📝 𝖳𝗈 𝖲𝖾𝗍 𝖢𝗎𝗌𝗍𝗈𝗆 𝖬𝖾𝗍𝖺𝖽𝖺𝗍𝖺</blockquote>

➲ /metadata: 𝖳𝗈 𝖲𝖾𝗍 𝖠 𝖢𝗎𝗌𝗍𝗈𝗆 𝖬𝖾𝗍𝖺𝖽𝖺𝗍𝖺

𝖠𝖿𝗍𝖾𝗋 𝖴𝗌𝗂𝗇𝗀 𝖢𝗆𝖽 𝖲𝖾𝗇𝖽 𝖠𝗇𝗒 𝖳𝖾𝗑𝗍 𝖨 𝖶𝗂𝗅𝗅 𝖲𝖺𝗏𝖾 𝖨𝗍 𝖠𝗌 𝖸𝗈𝗎𝗋 𝖬𝖾𝗍𝖺𝖽𝖺𝗍𝖺

» 𝖤𝗑: `@Sʜᴜꪜᴏ`"""
