import os
import re
import time
import math
import random
import asyncio
from urllib.parse import urlparse, unquote

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from .database import tb
from .utils import progress_for_pyrogram, humanbytes, convert, add_prefix_suffix
from .ffmpeg import fix_thumb, take_screen_shot, add_metadata
from .rename import clean_filename, MAX_FILE_SIZE
from config import Config

URL_REGEX = re.compile(r'^https?://\S+$')
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
COOLDOWN_SECONDS = 5 * 60  # 5 minutes, non-premium users only

# In-memory per-user state between "URL received" -> "filename given" -> "type selected"
# NOTE: resets if the bot restarts — acceptable, the user just re-sends the URL.
PENDING_URLS = {}


def get_filename_from_url(url, content_disposition=None):
    if content_disposition:
        match = re.search(r"filename\*?=(?:UTF-\d\'\'|\")?([^\";]+)", content_disposition)
        if match:
            name = unquote(match.group(1).strip('"'))
            if name:
                return name
    path = urlparse(url).path
    name = unquote(os.path.basename(path))
    return name or None


async def check_url(url):
    """Checks whether a URL is reachable/downloadable WITHOUT downloading the body.
    Returns (ok, status_or_error, size, filename)."""
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.head(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    size = int(resp.headers.get("Content-Length", 0) or 0)
                    filename = get_filename_from_url(url, resp.headers.get("Content-Disposition"))
                    return True, resp.status, size, filename
        except Exception:
            pass  # some servers block HEAD — fall back to a ranged GET below
        try:
            headers = {"Range": "bytes=0-0"}
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                if resp.status in (200, 206):
                    content_range = resp.headers.get("Content-Range")
                    if content_range and "/" in content_range:
                        size = int(content_range.split("/")[-1])
                    else:
                        size = int(resp.headers.get("Content-Length", 0) or 0)
                    filename = get_filename_from_url(url, resp.headers.get("Content-Disposition"))
                    return True, resp.status, size, filename
                return False, resp.status, 0, None
        except Exception as e:
            return False, str(e), 0, None


async def url_progress(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or (total and current == total):
        percentage = (current * 100 / total) if total else 0
        speed = current / diff if diff > 0 else 0
        eta = convert(int((total - current) / speed)) if (speed > 0 and total) else "..."
        bar = "".join(["▣" for _ in range(math.floor(percentage / 5))]) + \
              "".join(["▢" for _ in range(20 - math.floor(percentage / 5))])
        text = (
            f"{ud_type}\n\n{bar}\n\n"
            f"**♻️Progress:** {round(percentage, 2)}%\n"
            f"**⏳Done:** {humanbytes(current)} / {humanbytes(total) if total else 'Unknown'}\n"
            f"**🚀Speed:** {humanbytes(speed)}/s\n"
            f"**⏰ETA:** {eta}"
        )
        try:
            await message.edit(text)
        except Exception:
            pass


async def download_url_to_path(url, file_path, status_msg):
    start = time.time()
    downloaded = 0
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as resp:
            if resp.status not in (200, 206):
                raise Exception(f"Server returned status {resp.status}")
            total_size = int(resp.headers.get("Content-Length", 0) or 0)
            with open(file_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded > MAX_FILE_SIZE:
                        f.close()
                        os.remove(file_path)
                        raise Exception("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")
                    await url_progress(downloaded, total_size, "🚀 Downloading From URL...  ⚡", status_msg, start)


PLATFORM_REGEX = re.compile(r'(youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com)', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Step 1: user sends a URL -> validate it, then ask for the new filename
# ---------------------------------------------------------------------------
@Client.on_message(filters.private & filters.text & filters.regex(r'^https?://\S+$') & ~filters.reply & ~filters.regex(PLATFORM_REGEX))
async def url_upload_start(client, message):
    user_id = message.from_user.id

    ban_chk = await tb.is_banned(user_id)
    if ban_chk:
        return await message.reply("**ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ. ᴄᴏɴᴛᴀᴄᴛ @CallOwnerBot ᴛᴏ ʀᴇsᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇ!!**")

    is_prem = await tb.is_premium(user_id)
    if not is_prem:
        last = await tb.get_last_url_download(user_id)
        if last:
            elapsed = time.time() - last
            if elapsed < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - elapsed)
                mins, secs = divmod(remaining, 60)
                return await message.reply_text(
                    f"⏳ **Please Wait**\n\nYou can download another file via URL in **{mins}m {secs}s**.\n\n"
                    f"💎 Premium users skip this cooldown — use /premium to check your status.",
                    quote=True
                )

    url = message.text.strip()
    status = await message.reply_text("🔗 **Checking URL...**", quote=True)

    ok, status_or_err, size, filename = await check_url(url)
    if not ok:
        return await status.edit(f"**Error:** Couldn't access this link (`{status_or_err}`). Make sure it's a direct download link.")
    if size and size > MAX_FILE_SIZE:
        return await status.edit("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")

    ext = filename.rsplit(".", 1)[-1] if (filename and "." in filename) else "mkv"
    old_name_display = filename or url.rsplit("/", 1)[-1] or "file"
    await status.delete()

    prompt = await message.reply_text(
        text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{old_name_display}`",
        reply_to_message_id=message.id,
        reply_markup=ForceReply(True)
    )
    PENDING_URLS[user_id] = {"url": url, "ext": ext, "prompt_id": prompt.id}

    await asyncio.sleep(600)
    pending = PENDING_URLS.get(user_id)
    if pending and pending.get("prompt_id") == prompt.id:
        PENDING_URLS.pop(user_id, None)
        try:
            await prompt.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Step 2: user replies with the new filename -> ask Document or Video
# ---------------------------------------------------------------------------
@Client.on_message(filters.private & filters.reply & filters.text,group=2)
async def url_rename_reply(client, message):
    user_id = message.from_user.id
    pending = PENDING_URLS.get(user_id)
    reply_message = message.reply_to_message
    if not pending or not reply_message or reply_message.id != pending.get("prompt_id"):
        return  # not a URL-rename prompt — let the other reply handlers deal with it

    new_name = clean_filename(message.text)
    if "." not in new_name:
        new_name = f"{new_name}.{pending.get('ext', 'mkv')}"

    try:
        await reply_message.delete()
    except Exception:
        pass
    try:
        await message.delete()
    except Exception:
        pass

    pending["new_filename"] = new_name
    pending["prompt_id"] = None  # prompt consumed, stop the timeout-cleanup from deleting anything further

    buttons = [
        [InlineKeyboardButton("📁 Document", callback_data="urlget_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="urlget_video")],
    ]
    await client.send_message(
        chat_id=message.chat.id,
        text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------------------------------------------------------------------
# Step 3: user picks Document/Video -> download from URL and upload, once
# ---------------------------------------------------------------------------
@Client.on_callback_query(filters.regex("^urlget_"),group=2)
async def url_doc(bot, update):
    user_id = update.from_user.id
    pending = PENDING_URLS.pop(user_id, None)
    if not pending or "new_filename" not in pending:
        return await update.message.edit("⚠️ **This session has expired.** Please send the URL again.")

    url = pending["url"]
    new_filename_raw = pending["new_filename"]

    prefix = await tb.get_prefix(user_id)
    suffix = await tb.get_suffix(user_id)
    try:
        new_filename = add_prefix_suffix(new_filename_raw, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Something Went Wrong Can't Set Prefix/Suffix 🥺\n\n**Error:** `{e}`")

    os.makedirs(f"downloads/{user_id}", exist_ok=True)
    file_path = f"downloads/{user_id}/{new_filename}"

    ms = await update.message.edit("🚀 Try To Download...  ⚡")
    try:
        await download_url_to_path(url, file_path, ms)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return await ms.edit(f"**Error:** `{e}`")

    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
    _bool_metadata = await tb.get_metadata(user_id)
    if _bool_metadata:
        metadata_code = await tb.get_metadata_code(user_id)
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(file_path, metadata_path, metadata_code, ms)
    else:
        metadata_path = None
        await ms.edit("⏳ Mode Changing...  ⚡")

    duration = 0
    try:
        parser = createParser(file_path)
        meta = extractMetadata(parser)
        if meta.has("duration"):
            duration = meta.get('duration').seconds
        parser.close()
    except Exception:
        pass

    ph_path = None
    c_caption = await tb.get_caption(user_id)
    c_thumb = await tb.get_thumbnail(user_id)
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

    if c_caption:
        try:
            caption = c_caption.format(filename=new_filename, filesize=humanbytes(file_size), duration=convert(duration))
        except Exception as e:
            return await ms.edit(text=f"Your Caption Error: ({e})")
    else:
        caption = f"**{new_filename}**"
    if await tb.get_join_enabled(user_id):
        caption += "\n\n\n**[Join 👉@Bangla_Movie_ST]**"

    if c_thumb:
        ph_path = await bot.download_media(c_thumb)
        width, height, ph_path = await fix_thumb(ph_path)
    elif duration:
        try:
            ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, duration - 1))
            width, height, ph_path = await fix_thumb(ph_path_)
        except Exception as e:
            ph_path = None
            print(e)

    try:
        await ms.edit("💠 Try To Upload...  ⚡")
    except Exception:
        pass

    type_ = update.data.split("_")[1]
    close_button = InlineKeyboardMarkup([[InlineKeyboardButton("Join Now",url="https://t.me/Bangla_Movie_ST")]])
    try:
        if type_ == "document":
            sent_message = await bot.send_document(update.message.chat.id, document=metadata_path if _bool_metadata else file_path, thumb=ph_path, caption=caption, progress=progress_for_pyrogram, progress_args=("📤 Uploading...  ⚡", ms, time.time()), reply_markup=close_button)
        elif type_ == "video":
            sent_message = await bot.send_video(update.message.chat.id, video=metadata_path if _bool_metadata else file_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=("📤 Uploading...  ⚡", ms, time.time()), reply_markup=close_button)
        await bot.copy_message(chat_id=Config.BIN_CHANNEL, from_chat_id=update.message.chat.id, message_id=sent_message.id, caption=f"**File :-** `{new_filename}`\n**Uploaded By :-** {update.message.chat.first_name} (`{update.message.chat.id}`)", reply_markup=close_button)
        await tb.log_backup(user_id, sent_message.id, new_filename)
        await tb.increment_files_processed(user_id)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if ph_path and os.path.exists(ph_path):
            os.remove(ph_path)
        return await ms.edit(f"**Error:** `{e}`")

    await ms.delete()
    if ph_path and os.path.exists(ph_path):
        os.remove(ph_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    if not await tb.is_premium(user_id):
        await tb.set_last_url_download(user_id, time.time())
