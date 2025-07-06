from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient
from pyrogram import Client

import config


TEMP_MONGODB = "mongodb+srv://BADMUNDA:BADMYDAD@badhacker.i5nw9na.mongodb.net/"


if config.MONGO_URL is None:
    LOGGER(__name__).warning(
        "ʏᴏᴜʀ ᴍᴏɴɢᴏ ᴅᴇᴀᴅ, ʏᴏᴜʀ ʙᴏᴛ ᴡᴏʀᴋ ᴏɴ sʜɪᴢᴜᴄʜᴀᴛ ᴍᴏɴɢᴏ"
    )
    temp_client = Client(
        "shizuchatbot",
        bot_token=config.BOT_TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
    )
    temp_client.start()
    info = temp_client.get_me()
    username = info.username
    temp_client.stop()
    _mongo_async_ = _mongo_client_(TEMP_MONGODB)
    _mongo_sync_ = MongoClient(TEMP_MONGODB)
    mongodb = _mongo_async_[username]
    pymongodb = _mongo_sync_[username]
else:
    _mongo_async_ = _mongo_client_(config.MONGO_URL)
    _mongo_sync_ = MongoClient(config.MONGO_URL)
    mongodb = _mongo_async_.BADMUSIC
    pymongodb = _mongo_sync_.BADMUSIC
