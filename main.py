import logging
from telethon import TelegramClient, events, Button
from telethon.types import (
    UpdateNewMessage,
    MessageService,
    MessageActionRequestedPeerSentMe)
from config.config import Config, load_config
from lexicon.lexicon import LEXICON_RU
from keyboards.keyboard import selection_button_list, period_buttons

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format
)

api_id = config.api.api_id
api_hash = config.api.api_hash
username = config.api.user
bot_token = config.bot.token

bot_client = TelegramClient('bot', api_id, api_hash)
user_client = TelegramClient(username, api_id, api_hash)

user_sessions = {}

class UserSession:
    def __init__(self):
        self.selected_chat_id = None
        self.selected_chat_type = None
        self.selected_chat_username = None

chat_types = {1: "Channel", 2: "Group", 3: "User"}

def format_chat_info(select_peer, chat_type):
    chat_id = None
    if hasattr(select_peer, "user_id"):
        chat_id = select_peer.user_id
    elif hasattr(select_peer, "chat_id"):
        chat_id = -select_peer.chat_id
        chat_type = "Small Group"
    elif hasattr(select_peer, "channel_id"):
        if chat_type == "Group":
            chat_type = "Supergroup"
        chat_id = f"-100{select_peer.channel_id}"

    select_username = getattr(select_peer, "username", None)
    return chat_id, chat_type, select_username


@bot_client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    await event.respond(LEXICON_RU["/help"], buttons=None)


@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    user_sessions[user_id] = UserSession()

    selection_buttons = bot_client.build_reply_markup(selection_button_list)
    selection_buttons.resize = True

    await event.respond(LEXICON_RU["/start"], buttons=selection_buttons)

@bot_client.on(events.Raw(types=UpdateNewMessage))
async def get_selected_chat(event):
    message = event.message

    # пропускаем обычные сообщения
    if not isinstance(message, MessageService):
        return

    # обрабатываем только запросы к контактам / чатам
    if not hasattr(message.action, '__class__') or not isinstance(message.action, MessageActionRequestedPeerSentMe):
        return

    # обрабатываем сообщения конкретного пользователя (ID валидный)
    user_id = message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else None
    if not user_id:
        return

    await bot_client.delete_messages(message.peer_id, [message.id])
    chat = message.action.peers[0]

    chat_type = chat_types.get(message.action.button_id, "Unknown")

    chat_id, formatted_type, select_username = format_chat_info(chat, chat_type)

    # Сохраняем выбранный чат в сессии пользователя
    if user_id in user_sessions:
        user_sessions[user_id].selected_chat_id = chat_id
        user_sessions[user_id].selected_chat_type = formatted_type
        user_sessions[user_id].selected_chat_username = select_username

    chat_info = f"Вы выбрали `{formatted_type}` с ID: `{chat_id}`"
    if select_username:
        chat_info += f"\nUsername: @{select_username}"

    await bot_client.send_message(
        message.peer_id,
        chat_info,
        buttons=Button.clear()
    )

    await bot_client.send_message(
        entity=message.peer_id,
        message="Выберите срок службы сообщений для удаления:",
        buttons=period_buttons
    )


bot_client.start(bot_token=bot_token)
user_client.start()
bot_client.run_until_disconnected()
