import random
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from shizuchat.database.chats import add_served_chat
from shizuchat.database.users import add_served_user
from shizuchat.database import abuse_list, add_served_cchat, add_served_cuser, chatai
from config import MONGO_URL, OWNER_ID
from shizuchat import shizuchat, mongo, LOGGER, db
from shizuchat.idchatbot.helpers import languages
import asyncio

translator = GoogleTranslator()

lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status
abuse_words_db = db.abuse_words_db.words

replies_cache = []
abuse_cache = []
blocklist = {}
message_counts = {}


async def load_abuse_cache():
    global abuse_cache
    abuse_cache = [entry['word'] for entry in await abuse_words_db.find().to_list(length=None)]

async def add_abuse_word(word: str):
    global abuse_cache
    if word not in abuse_cache:
        await abuse_words_db.insert_one({"word": word})
        abuse_cache.append(word)

async def is_abuse_present(text: str):
    global abuse_cache
    if not abuse_cache:
        await load_abuse_cache()
    text_lower = text.lower()
    return any(word in text_lower for word in abuse_list) or any(word in text_lower for word in abuse_cache)

@Client.on_message(filters.command("block"))
async def request_block_word(client: Client, message: Message):
    try:
        if message.reply_to_message and message.reply_to_message.text:
            new_word = message.reply_to_message.text.split()[0].lower()
        elif len(message.command) >= 2:
            new_word = message.command[1].lower()
        else:
            await message.reply_text("**Usage:** Reply to a message or use `/block <word>` to request blocking a word.")
            return

        chat_name = message.chat.title if message.chat.title else "Private Chat"
        chat_username = f"@{message.chat.username}" if message.chat.username else "No Username"
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else f"`{user_id}`"
        message_id = message.id

        review_message = (
            f"**Block Request Received From {message.from_user.mention}**\n\n"
            f"**Word:** `{new_word}`\n"
            f"**Chat Name:** {chat_name}\n"
            f"**Chat ID:** `{chat_id}`\n"
            f"**Chat Username:** {chat_username}\n"
            f"**Requested By:** {username}\n"
            f"**Message ID:** `{message_id}`\n"
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_block:{new_word}:{chat_id}:{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_block:{new_word}:{chat_id}:{user_id}")
            ]
        ])

        await shizuchat.send_message(OWNER_ID, review_message, reply_markup=buttons)
        await message.reply_text(f"**Hey** {message.from_user.mention}\n\n**Your block request has been sent to owner for review.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_callback_query(filters.regex(r"^(accept_block|decline_block):"), group=-3)
async def handle_block_review(client: Client, callback: CallbackQuery):
    try:
        action, word, chat_id, user_id = callback.data.split(":")
        user_id = int(user_id)
        chat_id = int(chat_id)

        if action == "accept_block":
            await add_abuse_word(word)
            await callback.message.edit_text(f"✅ **Word '{word}' has been added to the abuse list.**")
            await client.send_message(chat_id, f"**Hello dear bot users,**\n**The word:- [ '{word}' ], has been approved by my owner for blocking and now added to blocklist.**\n\n**Thanks For Support, You can block more abusing type words by /block**")
        elif action == "decline_block":
            await callback.message.edit_text(f"❌ **Block request for the word '{word}' has been declined.**")
            await client.send_message(chat_id, f"**The block request for '{word}' has been declined by the Owner.**")
    except Exception as e:
        await callback.message.reply_text(f"Error: {e}")

@Client.on_message(filters.command("unblock") & filters.user(OWNER_ID))
async def unblock_word(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("**Usage:** `/unblock <word>`\nRemove a word from the abuse list.")
            return
        word_to_remove = message.command[1].lower()
        global abuse_cache
        if word_to_remove in abuse_cache:
            await abuse_words_db.delete_one({"word": word_to_remove})
            abuse_cache.remove(word_to_remove)
            await message.reply_text(f"**Word '{word_to_remove}' removed from abuse list!**")
        else:
            await message.reply_text(f"**Word '{word_to_remove}' is not in the abuse list.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command("blocked") & filters.user(OWNER_ID))
async def list_blocked_words(client: Client, message: Message):
    try:
        global abuse_cache
        if not abuse_cache:
            await load_abuse_cache()
        if abuse_cache:
            blocked_words = ", ".join(abuse_cache)
            await message.reply_text(f"**Blocked Words:**\n{blocked_words}")
        else:
            await message.reply_text("**No blocked words found.**")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

async def save_reply(original_message: Message, reply_message: Message):
    global replies_cache
    try:
        if (original_message.text and await is_abuse_present(original_message.text)) or \
           (reply_message.text and await is_abuse_present(reply_message.text)):
            return
        
        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            reply_data["text"] = reply_message.sticker.file_id
            reply_data["check"] = "sticker"
        elif reply_message.photo:
            reply_data["text"] = reply_message.photo.file_id
            reply_data["check"] = "photo"
        elif reply_message.video:
            reply_data["text"] = reply_message.video.file_id
            reply_data["check"] = "video"
        elif reply_message.audio:
            reply_data["text"] = reply_message.audio.file_id
            reply_data["check"] = "audio"
        elif reply_message.animation:
            reply_data["text"] = reply_message.animation.file_id
            reply_data["check"] = "gif"
        elif reply_message.voice:
            reply_data["text"] = reply_message.voice.file_id
            reply_data["check"] = "voice"
        elif reply_message.text:
            translated_text = reply_message.text
            reply_data["text"] = translated_text
            reply_data["check"] = "none"

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def load_replies_cache():
    global replies_cache
    replies_cache = await chatai.find().to_list(length=None)
    await load_abuse_cache()

async def remove_abusive_reply(reply_data):
    global replies_cache
    await chatai.delete_one(reply_data)
    replies_cache = [reply for reply in replies_cache if reply != reply_data]

async def get_reply(word: str):
    global replies_cache
    if not replies_cache:
        await load_replies_cache()
        
    relevant_replies = [reply for reply in replies_cache if reply['word'] == word]
    for reply in relevant_replies:
        if reply.get('text') and await is_abuse_present(reply['text']):
            await remove_abusive_reply(reply)
    if not relevant_replies:
        relevant_replies = replies_cache
    return random.choice(relevant_replies) if relevant_replies else None


async def get_chat_language(chat_id, bot_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id, "bot_id": bot_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None
    
@Client.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        bot_id = client.me.id
        chat_status = await status_db.find_one({"chat_id": chat_id, "bot_id": bot_id})
        
        if chat_status and chat_status.get("status") == "disabled":
            return

        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                return await add_served_chat(message.chat.id)
            else:
                return await add_served_user(message.chat.id)

        if ((message.reply_to_message and message.reply_to_message.from_user.id == client.me.id) or not message.reply_to_message) and not message.from_user.is_bot:
            reply_data = await get_reply(message.text)

            if reply_data:
                response_text = reply_data["text"]
                chat_lang = await get_chat_language(chat_id, bot_id)

                if not chat_lang or chat_lang == "nolang":
                    translated_text = response_text
                else:
                    translated_text = GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                    if not translated_text:
                        translated_text = response_text
                if reply_data["check"] == "sticker":
                    try:
                        await message.reply_sticker(reply_data["text"])
                    except:
                        pass
                elif reply_data["check"] == "photo":
                    try:
                        await message.reply_photo(reply_data["text"])
                    except:
                        pass
                elif reply_data["check"] == "video":
                    try:
                        await message.reply_video(reply_data["text"])
                    except:
                        pass
                elif reply_data["check"] == "audio":
                    try:
                        await message.reply_audio(reply_data["text"])
                    except:
                        pass
                elif reply_data["check"] == "gif":
                    try:
                        await message.reply_animation(reply_data["text"])
                    except:
                        pass
                elif reply_data["check"] == "voice":
                    try:
                        await message.reply_voice(reply_data["text"])
                    except:
                        pass
                else:
                    try:
                        await message.reply_text(translated_text)
                    except:
                        pass
            else:
                try:
                    await message.reply_text("**I don't understand. What are you saying?**")
                except:
                    pass

        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        try:
            await message.reply_text("🙄🙄")
        except:
            pass
    except Exception as e:
        return
