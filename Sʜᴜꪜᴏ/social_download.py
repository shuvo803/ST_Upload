import os
import re
import time
import random
import asyncio

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup

from .database import tb
from .utils import progress_for_pyrogram, humanbytes, convert, add_prefix_suffix
from .ffmpeg import fix_thumb, take_screen_shot, add_metadata
from .rename import clean_filename, MAX_FILE_SIZE
from config import Config

YOUTUBE_REGEX = re.compile(r'^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/\S+$', re.IGNORECASE)
FB_TIKTOK_REGEX = re.compile(r'^https?://(www\.|m\.|vm\.|vt\.)?(facebook\.com|fb\.watch|tiktok\.com)/\S+$', re.IGNORECASE)
PLATFORM_REGEX = re.compile(
    r'^https?://(www\.|m\.|vm\.|vt\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com)/\S+$',
    re.IGNORECASE
)
COOLDOWN_SECONDS = 5 * 60  # shared with url_upload.py's cooldown (same DB fields)

# In-memory per-user state, used only for the YouTube flow (which still asks filename/type).
PENDING_YT = {}


def is_platform_url(text):
    return bool(text) and bool(PLATFORM_REGEX.match(text.strip()))


def is_fb_or_tiktok(text):
    return bool(text) and bool(FB_TIKTOK_REGEX.match(text.strip()))


def _detect_platform(url):
    """Detect platform from URL."""
    url_lower = url.lower()
    if 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    return None


async def ytdlp_download(url, out_dir, platform=None):
    """Runs the blocking yt-dlp download in a thread so it doesn't block the event loop.

    For TikTok: uses custom headers, extractor args, cookies support, and fallback mechanism
    to handle videos where download is disabled or restricted.
    """
    loop = asyncio.get_event_loop()
    result = {}

    def _try_download(ydl_opts):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if not os.path.exists(path):
                base = os.path.splitext(path)[0]
                for ext in ('mp4', 'mkv', 'webm'):
                    if os.path.exists(f"{base}.{ext}"):
                        path = f"{base}.{ext}"
                        break
            result['path'] = path
            result['title'] = info.get('title') or 'video'
            result['duration'] = int(info.get('duration') or 0)
            return True

    def run():
        base_opts = {
            'outtmpl': f'{out_dir}/%(id)s.%(ext)s',
            'format': 'bestvideo[filesize<1900M]+bestaudio/best[filesize<1900M]/best',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        # ─── টিকটকের জন্য বিশেষ সেটআপ ───
        if platform == 'tiktok':
            # প্রথম চেষ্টা: ডেস্কটপ হেডার + ওয়েবপেজ এক্সট্রাকশন
            tiktok_opts = base_opts.copy()
            tiktok_opts.update({
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.tiktok.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                'extractor_args': {
                    'tiktok': {
                        'webpage_download': True,
                    }
                }
            })
            # যদি cookies.txt ফাইল থাকে (লগইন করা অবস্থা), তাহলে সেটা ব্যবহার করবে
            if os.path.exists('cookies.txt'):
                tiktok_opts['cookies'] = 'cookies.txt'

            try:
                return _try_download(tiktok_opts)
            except Exception as first_err:
                # দ্বিতীয় চেষ্টা: মোবাইল হেডার + সিম্পল ফরম্যাট
                try:
                    fallback_opts = base_opts.copy()
                    fallback_opts['format'] = 'best[filesize<1900M]/best'
                    fallback_opts['http_headers'] = {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                        'Referer': 'https://m.tiktok.com/',
                    }
                    return _try_download(fallback_opts)
                except Exception as second_err:
                    raise Exception(f"Primary: {first_err} | Fallback: {second_err}")

        # ইউটিউব/ফেসবুকের জন্য স্বাভাবিক ডাউনলোড
        return _try_download(base_opts)

    await loop.run_in_executor(None, run)
    return result


async def process_and_upload(bot, chat_id, user_id, file_path, duration, ms, close_button, first_name):
    """Shared final step: metadata, thumbnail, caption, upload as video, backup, stats."""
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
    _bool_metadata = await tb.get_metadata(user_id)
    new_filename = os.path.basename(file_path)
    if _bool_metadata:
        metadata_code = await tb.get_metadata_code(user_id)
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(file_path, metadata_path, metadata_code, ms)
    else:
        metadata_path = None

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
            ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, max(duration - 1, 0)))
            width, height, ph_path = await fix_thumb(ph_path_)
        except Exception as e:
            ph_path = None
            print(e)

    try:
        sent_message = await bot.send_video(chat_id, video=metadata_path if _bool_metadata else file_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=("📤 Uploading...  ⚡", ms, time.time()), reply_markup=close_button)
        await bot.copy_message(chat_id=Config.BIN_CHANNEL, from_chat_id=chat_id, message_id=sent_message.id, caption=f"**File :-** `{new_filename}`\n**Uploaded By :-** {first_name} (`{user_id}`)", reply_markup=close_button)
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


# ---------------------------------------------------------------------------
# Entry point: user sends a YouTube/Facebook/TikTok link
# ---------------------------------------------------------------------------
@Client.on_message(filters.private & filters.text & filters.create(lambda _, __, m: is_platform_url(m.text)) & ~filters.reply)
async def platform_download_start(client, message):
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
                    f"⏳ **Please Wait**\n\nYou can download another file in **{mins}m {secs}s**.\n\n"
                    f"💎 Premium users skip this cooldown — use /premium to check your status.",
                    quote=True
                )

    url = message.text.strip()
    status = await message.reply_text(
        "⬇️ **Downloading Video...**  ⚡\n\nThis can take a while depending on the video length.",
        quote=True
    )

    # প্ল্যাটফর্ম শনাক্ত করুন
    platform = _detect_platform(url)

    os.makedirs(f"downloads/{user_id}", exist_ok=True)
    try:
        result = await ytdlp_download(url, f"downloads/{user_id}", platform=platform)
    except Exception as e:
        error_msg = f"**Error:** `{e}`\n\n"
        if platform == 'tiktok':
            error_msg += (
                "টিকটক ভিডিওটি ডাউনলোড করা যাচ্ছে না। কারণগুলো হতে পারে:\n"
                "• ভিডিওটি প্রাইভেট বা ডিলিট করা হয়েছে\n"
                "• টিকটক সার্ভার রিকোয়েস্ট ব্লক করছে\n"
                "• ভিডিওটি শুধু লগইন করা ব্যবহারকারীদের জন্য\n\n"
                "💡 **টিপস:** `cookies.txt` ফাইল রুট ফোল্ডারে রাখুন (ঐচ্ছিক)।"
            )
        else:
            error_msg += "Make sure the video is public and not age/region restricted."
        return await status.edit(error_msg)

    path = result.get('path')
    if not path or not os.path.exists(path):
        return await status.edit("**Error:** Couldn't download this video (it may be private, restricted, or removed).")

    if os.path.getsize(path) > MAX_FILE_SIZE:
        os.remove(path)
        return await status.edit("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")

    close_button = InlineKeyboardMarkup([[InlineKeyboardButton("Join Now", url="https://t.me/Bangla_Movie_ST")]])

    # Facebook & TikTok: send straight away, no rename/type prompt.
    if is_fb_or_tiktok(url):
        prefix = await tb.get_prefix(user_id)
        suffix = await tb.get_suffix(user_id)
        raw_name = clean_filename(result['title']) or "video"
        if "." not in raw_name:
            raw_name += ".mp4"
        try:
            final_name = add_prefix_suffix(raw_name, prefix, suffix)
        except Exception:
            final_name = raw_name
        final_path = f"downloads/{user_id}/{final_name}"
        try:
            os.rename(path, final_path)
        except Exception:
            final_path = path
        await status.edit("🚀 Try To Process...  ⚡")
        return await process_and_upload(client, message.chat.id, user_id, final_path, result.get('duration', 0), status, close_button, message.from_user.first_name)

    # YouTube: keep the interactive rename + type-selection flow.
    await status.delete()
    prompt = await message.reply_text(
        text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{result['title']}`",
        reply_to_message_id=message.id,
        reply_markup=ForceReply(True)
    )
    PENDING_YT[user_id] = {"path": path, "duration": result.get('duration', 0), "prompt_id": prompt.id}

    await asyncio.sleep(600)
    pending = PENDING_YT.get(user_id)
    if pending and pending.get("prompt_id") == prompt.id:
        PENDING_YT.pop(user_id, None)
        if os.path.exists(pending["path"]):
            os.remove(pending["path"])
        try:
            await prompt.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# YouTube Step 2: user replies with the new filename -> ask Document or Video
# ---------------------------------------------------------------------------
@Client.on_message(filters.private & filters.reply & filters.text, group=5)
async def yt_rename_reply(client, message):
    user_id = message.from_user.id
    pending = PENDING_YT.get(user_id)
    reply_message = message.reply_to_message
    if not pending or not reply_message or reply_message.id != pending.get("prompt_id"):
        return  # not our prompt — let the other reply handlers deal with it

    new_name = clean_filename(message.text)
    if "." not in new_name:
        new_name = f"{new_name}.mp4"

    try:
        await reply_message.delete()
    except Exception:
        pass
    try:
        await message.delete()
    except Exception:
        pass

    pending["new_filename"] = new_name
    pending["prompt_id"] = None

    buttons = [
        [InlineKeyboardButton("📁 Document", callback_data="ytget_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="ytget_video")],
    ]
    await client.send_message(
        chat_id=message.chat.id,
        text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------------------------------------------------------------------
# YouTube Step 3: user picks Document/Video -> process and upload
# ---------------------------------------------------------------------------
@Client.on_callback_query(filters.regex("^ytget_"), group=5)
async def yt_doc(bot, update):
    user_id = update.from_user.id
    pending = PENDING_YT.pop(user_id, None)
    if not pending or "new_filename" not in pending:
        return await update.message.edit("⚠️ **This session has expired.** Please send the link again.")

    downloaded_path = pending["path"]
    duration = pending.get("duration", 0)
    new_filename_raw = pending["new_filename"]

    prefix = await tb.get_prefix(user_id)
    suffix = await tb.get_suffix(user_id)
    try:
        new_filename = add_prefix_suffix(new_filename_raw, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Something Went Wrong Can't Set Prefix/Suffix 🥺\n\n**Error:** `{e}`")

    file_path = f"downloads/{user_id}/{new_filename}"
    try:
        os.rename(downloaded_path, file_path)
    except Exception:
        file_path = downloaded_path  # fallback: keep the downloaded name if rename fails

    ms = await update.message.edit("🚀 Try To Process...  ⚡")

    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
    _bool_metadata = await tb.get_metadata(user_id)
    if _bool_metadata:
        metadata_code = await tb.get_metadata_code(user_id)
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(file_path, metadata_path, metadata_code, ms)
    else:
        metadata_path = None

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
            ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, max(duration - 1, 0)))
            width, height, ph_path = await fix_thumb(ph_path_)
        except Exception as e:
            ph_path = None
            print(e)

    type_ = update.data.split("_")[1]
    close_button = InlineKeyboardMarkup([[InlineKeyboardButton("Join Now", url="https://t.me/Bangla_Movie_ST")]])
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
