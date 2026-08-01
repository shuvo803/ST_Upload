import os
import re
import time
import math
import asyncio
from urllib.parse import urlparse, unquote

import aiohttp
from pyrogram import Client, filters

from .database import tb
from .utils import humanbytes, TimeFormatter
from .rename import ask_new_filename, clean_filename, MAX_FILE_SIZE

URL_REGEX = re.compile(r'^https?://\S+$')
CHUNK_SIZE = 1024 * 1024  # 1MB


def get_filename_from_url(url, content_disposition=None):
    if content_disposition:
        match = re.search(r"filename\*?=(?:UTF-\d\'\'|\")?([^\";]+)", content_disposition)
        if match:
            name = unquote(match.group(1).strip('"'))
            if name:
                return name
    path = urlparse(url).path
    name = unquote(os.path.basename(path))
    if not name or "." not in name:
        name = f"file_{int(time.time())}.bin"
    return name


async def url_progress(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or (total and current == total):
        percentage = (current * 100 / total) if total else 0
        speed = current / diff if diff > 0 else 0
        eta = TimeFormatter(int(((total - current) / speed) * 1000)) if (speed > 0 and total) else "..."
        bar = "".join(["▣" for _ in range(math.floor(percentage / 5))]) + \
              "".join(["▢" for _ in range(20 - math.floor(percentage / 5))])
        text = (
            f"{ud_type}\n\n{bar}\n\n"
            f"**Progress:** {round(percentage, 2)}%\n"
            f"**Done:** {humanbytes(current)} / {humanbytes(total) if total else 'Unknown'}\n"
            f"**Speed:** {humanbytes(speed)}/s\n"
            f"**ETA:** {eta}"
        )
        try:
            await message.edit(text)
        except Exception:
            pass


@Client.on_message(filters.private & filters.text & filters.regex(r'^https?://\S+$') & ~filters.reply)
async def url_upload_start(client, message):
    ban_chk = await tb.is_banned(int(message.from_user.id))
    if ban_chk:
        return await message.reply("**ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ. ᴄᴏɴᴛᴀᴄᴛ @CallOwnerBot ᴛᴏ ʀᴇsᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇ!!**")

    url = message.text.strip()
    status = await message.reply_text("🔗 **Checking URL...**", quote=True)

    user_dir = f"downloads/{message.from_user.id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = None

    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status != 200:
                    return await status.edit(f"**Error:** Link returned status `{resp.status}`. Make sure it's a direct download link.")

                total_size = int(resp.headers.get("Content-Length", 0) or 0)
                if total_size and total_size > MAX_FILE_SIZE:
                    return await status.edit("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")

                filename = clean_filename(get_filename_from_url(url, resp.headers.get("Content-Disposition")))
                file_path = f"{user_dir}/{filename}"

                start = time.time()
                downloaded = 0
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > MAX_FILE_SIZE:
                            f.close()
                            os.remove(file_path)
                            return await status.edit("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")
                        await url_progress(downloaded, total_size, "🔗 Downloading From URL...  ⚡", status, start)
    except asyncio.TimeoutError:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return await status.edit("**Error:** Download timed out. Check the link and try again.")
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return await status.edit(f"**Error:** `{e}`")

    try:
        await status.edit("💠 **Uploading To Telegram...**  ⚡")
        sent = await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            file_name=filename,
            progress=url_progress,
            progress_args=("💠 Uploading To Telegram...  ⚡", status, time.time()),
        )
    except Exception as e:
        return await status.edit(f"**Error While Uploading:** `{e}`")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    await status.delete()
    await ask_new_filename(client, sent, filename)
