import time

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.message import Message
from telegram.update import Update
from telegram.error import TimedOut, BadRequest, RetryAfter

from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, status_reply_dict, status_reply_dict_lock, \
                Interval, DOWNLOAD_STATUS_UPDATE_INTERVAL, LOG_CHANNEL_ID, LOG_SEND_TEXT, LOG_CHANNEL_LINK
from bot.helper.ext_utils.bot_utils import get_readable_message, setInterval


def sendMessage(text: str, bot, update: Update):
    try:
        return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, allow_sending_without_reply=True, parse_mode='HTMl', disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.error(str(r))
        time.sleep(r.retry_after)
        return sendMessage(text, bot, update)
    except Exception as e:
        LOGGER.error(str(e))

def sendMarkup(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    try:
        return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, reply_markup=reply_markup, allow_sending_without_reply=True,
                            parse_mode='HTMl', disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.error(str(r))
        time.sleep(r.retry_after)
        return sendMarkup(text, bot, update, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))


def sendLog(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    try:
        return bot.send_message(f"{LOG_CHANNEL_ID}",
                             reply_to_message_id=update.message.message_id,
                             text=text, disable_web_page_preview=True, reply_markup=reply_markup, allow_sending_without_reply=True, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))

def sendtextlog(text: str, bot, update: Update):
    try:
        return bot.send_message(f"{LOG_SEND_TEXT}",
                             reply_to_message_id=update.message.message_id,
                             text=text, disable_web_page_preview=True, allow_sending_without_reply=True, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def sendPrivate(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    bot_d = bot.get_me()
    b_uname = bot_d.username
    
    try:
        return bot.send_message(update.message.from_user.id,
                             reply_to_message_id=update.message.message_id,
                             text=text, disable_web_page_preview=True, reply_markup=reply_markup, allow_sending_without_reply=True, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))
        if "Forbidden" in str(e):
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            botstart = f"http://t.me/{b_uname}?start=start"
            keyboard = [
            [InlineKeyboardButton("𝐒𝐓𝐀𝐑𝐓 𝐌𝐄", url = f"{botstart}")],
            [InlineKeyboardButton("𝐉𝐎𝐈𝐍 𝐇𝐄𝐑𝐄", url = f"{LOG_CHANNEL_LINK}")]]
            sendMarkup(f"𝙳𝙴𝙰𝚁 {uname},\n\n<b>ɪ ғᴏᴜɴᴅ ᴛʜᴀᴛ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ sᴛᴀʀᴛᴇᴅ ᴍᴇ ɪɴ ᴘᴍ (ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ) ʏᴇᴛ.</b>\n\n𝐅𝐑𝐎𝐌 𝐍𝐎𝐖 𝐎𝐍 𝐈 𝐖𝐈𝐋𝐋 𝐆𝐈𝐕𝐄 𝐋𝐈𝐍𝐊 𝐈𝐍 𝐏𝐌 (𝐏𝐑𝐈𝐕𝐀𝐓𝐄 𝐂𝐇𝐀𝐓) 𝐀𝐍𝐃 𝐋𝐎𝐆 𝐂𝐇𝐀𝐍𝐍𝐄𝐋 𝐎𝐍𝐋𝐘", bot, update, reply_markup=InlineKeyboardMarkup(keyboard))
            return


def editMessage(text: str, message: Message, reply_markup=None):
    try:
        bot.edit_message_text(text=text, message_id=message.message_id,
                              chat_id=message.chat.id,reply_markup=reply_markup,
                              parse_mode='HTMl', disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.error(str(r))
        time.sleep(r.retry_after)
        return editMessage(text, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))

def deleteMessage(bot, message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))

def sendLogFile(bot, update: Update):
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                          reply_to_message_id=update.message.message_id,
                          chat_id=update.message.chat_id)

def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass

def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))

def update_all_messages():
    msg, buttons = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                if buttons == "":
                    editMessage(msg, status_reply_dict[chat_id])
                else:
                    editMessage(msg, status_reply_dict[chat_id], buttons)
                status_reply_dict[chat_id].text = msg

def sendStatusMessage(msg, bot):
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
    progress, buttons = get_readable_message()
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                deleteMessage(bot, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        if buttons == "":
            message = sendMessage(progress, bot, msg)
        else:
            message = sendMarkup(progress, bot, msg, buttons)
        status_reply_dict[msg.message.chat.id] = message
