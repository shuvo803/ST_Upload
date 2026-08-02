from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from .database import tb

# Per-user "waiting for the next .srt upload" flag (in-memory, resets on restart — acceptable)
PENDING_SUBTITLE = set()

ON = [[InlineKeyboardButton('Subtitle Embed On ✅', callback_data='subtitle_1')], [InlineKeyboardButton('Set New Subtitle', callback_data='set_subtitle')]]
OFF = [[InlineKeyboardButton('Subtitle Embed Off ❌', callback_data='subtitle_0')], [InlineKeyboardButton('Set New Subtitle', callback_data='set_subtitle')]]
NONE_SET = [[InlineKeyboardButton('Set Subtitle (.srt)', callback_data='set_subtitle')]]


@Client.on_message(filters.private & filters.command('subtitle'))
async def subtitle_status(bot: Client, message: Message):
    srt_file_id = await tb.get_subtitle(message.from_user.id)
    if not srt_file_id:
        return await message.reply_text(
            "**You haven't set a subtitle file yet.**\n\nSend an `.srt` file after tapping the button below, "
            "and it'll be embedded into every video you rename (as a soft subtitle track) until you turn it off.",
            reply_markup=InlineKeyboardMarkup(NONE_SET)
        )
    enabled = await tb.get_subtitle_enabled(message.from_user.id)
    await message.reply_text(
        "**Your Subtitle Settings**",
        reply_markup=InlineKeyboardMarkup(ON if enabled else OFF)
    )


@Client.on_callback_query(filters.regex('^(subtitle_|set_subtitle)'), group=4)
async def subtitle_callback(bot: Client, query):
    data = query.data
    if data == 'set_subtitle':
        PENDING_SUBTITLE.add(query.from_user.id)
        await query.message.edit("**Please send your `.srt` subtitle file now.**\n\nIt'll be saved and auto-embedded into your renamed videos.")
        return
    _bool = data.split('_')[1]
    if bool(eval(_bool)):
        await tb.set_subtitle_enabled(query.from_user.id, False)
        await query.message.edit("**Your Subtitle Settings**", reply_markup=InlineKeyboardMarkup(OFF))
    else:
        await tb.set_subtitle_enabled(query.from_user.id, True)
        await query.message.edit("**Your Subtitle Settings**", reply_markup=InlineKeyboardMarkup(ON))


@Client.on_message(filters.private & filters.document, group=-1)
async def catch_subtitle_upload(client, message: Message):
    user_id = message.from_user.id
    if user_id not in PENDING_SUBTITLE:
        return  # not expecting a subtitle right now — let the normal rename handler take this document
    file_name = message.document.file_name or ""
    if not file_name.lower().endswith(".srt"):
        return await message.reply_text("That's not an `.srt` file. Please send a valid `.srt` subtitle file, or use /subtitle to cancel.")
    PENDING_SUBTITLE.discard(user_id)
    await tb.set_subtitle(user_id, message.document.file_id)
    await message.reply_text("**✅ Subtitle Saved & Enabled!**\n\nIt'll now be embedded into videos you rename (Video output type only). Use /subtitle to turn it off anytime.")
    message.stop_propagation()
