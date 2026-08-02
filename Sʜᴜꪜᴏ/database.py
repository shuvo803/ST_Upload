import motor.motor_asyncio
import time
from config import Config
from .utils import send_log

class Sʜᴜꪜᴏ:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.tb = self._client[database_name]
        self.col = self.tb.user
        self.bannedList = self.tb.bannedList
        self.backups = self.tb.backups

    def new_user(self, id):
        return dict(
            _id=int(id),
            file_id=None,
            caption=None,
            prefix=None,
            suffix=None,
            metadata=False,
            metadata_code="By :- @Sʜᴜꪜᴏ",
            premium_until=None,
            last_url_download=None,
            subtitle_file_id=None,
            subtitle_enabled=False,
            last_seen=time.time(),
            files_processed=0
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)            
            await send_log(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({'_id': int(user_id)})

    #======================= Thumbnail ========================#

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('file_id', None)

    #======================= Caption ========================#

    async def set_caption(self, id, caption):
        await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('caption', None)

    #======================= Prefix ========================#

    async def set_prefix(self, id, prefix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})  

    async def get_prefix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('prefix', None)

    #======================= Suffix ========================#

    async def set_suffix(self, id, suffix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})  

    async def get_suffix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('suffix', None)

    #======================= Metadata ========================#

    async def set_metadata(self, id, bool_meta):
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata': bool_meta}})

    async def get_metadata(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('metadata', None)

    #======================= Metadata Code ========================#    

    async def set_metadata_code(self, id, metadata_code):
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata_code': metadata_code}})

    async def get_metadata_code(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('metadata_code', None)
 
    #======================= Ban User ========================#

    async def ban_user(self, user_id):
        user = await self.bannedList.find_one({'banId': int(user_id)})
        if user:
            return False
        else:
            await self.bannedList.insert_one({'banId': int(user_id)})
            return True

    async def is_banned(self, user_id):
        user = await self.bannedList.find_one({'banId': int(user_id)})
        return True if user else False
    
    async def is_unbanned(self, user_id):
        try: 
            if await self.bannedList.find_one({'banId': int(user_id)}):
                await self.bannedList.delete_one({'banId': int(user_id)})
                return True
            else:
                return False
        except Exception as e:
            e = f'Fᴀɪʟᴇᴅ ᴛᴏ ᴜɴʙᴀɴ.Rᴇᴀsᴏɴ : {e}'
            print(e)
            return e

    #======================= Premium ========================#

    async def add_premium(self, user_id, months):
        """Extends existing premium if still active, otherwise starts fresh from now."""
        now = time.time()
        user = await self.col.find_one({'_id': int(user_id)})
        current_until = (user or {}).get('premium_until')
        base = current_until if (current_until and current_until > now) else now
        new_until = base + (months * 30 * 24 * 60 * 60)
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'premium_until': new_until}}, upsert=True)
        return new_until

    async def remove_premium(self, user_id):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'premium_until': None}})

    async def is_premium(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        until = (user or {}).get('premium_until')
        return bool(until and until > time.time())

    async def get_premium_until(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return (user or {}).get('premium_until')

    #======================= URL Download Cooldown ========================#

    async def set_last_url_download(self, user_id, ts):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'last_url_download': ts}}, upsert=True)

    async def get_last_url_download(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return (user or {}).get('last_url_download')

    #======================= Subtitle ========================#

    async def set_subtitle(self, id, file_id):
        await self.col.update_one({'_id': int(id)}, {'$set': {'subtitle_file_id': file_id, 'subtitle_enabled': True}}, upsert=True)

    async def get_subtitle(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return (user or {}).get('subtitle_file_id')

    async def set_subtitle_enabled(self, id, bool_val):
        await self.col.update_one({'_id': int(id)}, {'$set': {'subtitle_enabled': bool_val}}, upsert=True)

    async def get_subtitle_enabled(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return (user or {}).get('subtitle_enabled', False)

    #======================= Stats (last seen / files processed) ========================#

    async def update_last_seen(self, id):
        await self.col.update_one({'_id': int(id)}, {'$set': {'last_seen': time.time()}}, upsert=True)

    async def get_active_today_count(self):
        cutoff = time.time() - 86400
        count = await self.col.count_documents({'last_seen': {'$gte': cutoff}})
        return count

    async def increment_files_processed(self, id):
        await self.col.update_one({'_id': int(id)}, {'$inc': {'files_processed': 1}}, upsert=True)

    async def get_total_files_processed(self):
        cursor = self.col.aggregate([{'$group': {'_id': None, 'total': {'$sum': '$files_processed'}}}])
        result = await cursor.to_list(length=1)
        return result[0]['total'] if result else 0

    #======================= Backup Tagging (BIN_CHANNEL, user-wise) ========================#

    async def log_backup(self, user_id, message_id, filename):
        await self.backups.insert_one({'user_id': int(user_id), 'message_id': message_id, 'filename': filename, 'timestamp': time.time()})

    async def get_user_backups(self, user_id, limit=20):
        cursor = self.backups.find({'user_id': int(user_id)}).sort('timestamp', -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_user_backup_count(self, user_id):
        return await self.backups.count_documents({'user_id': int(user_id)})


tb = Sʜᴜꪜᴏ(Config.DATABASE_URL, Config.DATABASE_NAME)
