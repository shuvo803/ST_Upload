from pyrogram import Client,filters
from pyrogram.types import Message,CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup,ForceReply
from .database import tb
from config import Txt
import asyncio

ON=[[InlineKeyboardButton('Metadata On ✅',callback_data='metadata_1')],[InlineKeyboardButton('Set Custom Metadata',callback_data='custom_metadata')]]
OFF=[[InlineKeyboardButton('Metadata Off ❌',callback_data='metadata_0')],[InlineKeyboardButton('Set Custom Metadata',callback_data='custom_metadata')]]

@Client.on_message(filters.private & filters.command('metadata'))
async def handle_metadata(bot:Client,message:Message):
    ms=await message.reply_text("**Please Wait...**",reply_to_message_id=message.id)
    bool_metadata=await tb.get_metadata(message.from_user.id)
    user_metadata=await tb.get_metadata_code(message.from_user.id)
    await ms.delete()
    if bool_metadata:
        return await message.reply_text(f"**Your Current Metadata :-**\n\n➜ `{user_metadata}` ",quote=True,reply_markup=InlineKeyboardMarkup(ON))
    return await message.reply_text(f"**Your Current Metadata :-**\n\n➜ `{user_metadata}` ",quote=True,reply_markup=InlineKeyboardMarkup(OFF))

@Client.on_callback_query(filters.regex('.*?(custom_metadata|metadata).*?'))
async def query_metadata(bot:Client,query:CallbackQuery):
    data=query.data
    if data.startswith('metadata_'):
        _bool=data.split('_')[1]
        user_metadata=await tb.get_metadata_code(query.from_user.id)
        if bool(eval(_bool)):
            await tb.set_metadata(query.from_user.id,bool_meta=False)
            await query.message.edit(f"**Your Current Metadata :-**\n\n➜ `{user_metadata}` ",reply_markup=InlineKeyboardMarkup(OFF))
        else:
            await tb.set_metadata(query.from_user.id,bool_meta=True)
            await query.message.edit(f"**Your Current Metadata :-**\n\n➜ `{user_metadata}` ",reply_markup=InlineKeyboardMarkup(ON))
    elif data=='custom_metadata':
        await query.message.delete()
        try:
            prompt=await query.message.reply_text(text=Txt.SEND_METADATA,disable_web_page_preview=True,reply_markup=ForceReply(True))
        except Exception as e:
            print(f"Error in query_metadata: {e}")
            return
        await asyncio.sleep(30)
        try:
            await prompt.delete()
        except Exception:
            pass

@Client.on_message(filters.private & filters.reply & filters.text)
async def metadata_reply(client,message:Message):
    reply_message=message.reply_to_message
    if not (reply_message and reply_message.reply_markup and isinstance(reply_message.reply_markup,ForceReply)):
        return
    if reply_message.text!=Txt.SEND_METADATA:
        return  # not the metadata prompt (e.g. the rename prompt) — let its own handler deal with it
    metadata_code=message.text
    ms=await message.reply_text("**Please Wait...**",reply_to_message_id=message.id)
    await tb.set_metadata_code(message.from_user.id,metadata_code=metadata_code)
    await ms.edit("**Your Metadata Code Set Successfully ✅**")
