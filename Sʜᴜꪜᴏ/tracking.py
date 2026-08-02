from pyrogram import Client, filters
from .database import tb

@Client.on_message(filters.private & filters.incoming, group=-5)
async def track_activity(client, message):
    if message.from_user:
        await tb.update_last_seen(message.from_user.id)
