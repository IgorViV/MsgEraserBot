import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient, events, Button, utils
from telethon.types import (
    UpdateNewMessage,
    MessageService,
    MessageActionRequestedPeerSentMe)
from telethon.tl.types import (
    User,
    Chat,
    Channel,
    Message,
    RequestedPeerChannel,
    RequestedPeerChat,
    RequestedPeerUser)
from config.config import Config, load_config
from lexicon.lexicon import LEXICON_RU
from keyboards.keyboard import selection_button_list, period_buttons

import getpass
from telethon.errors import SessionPasswordNeededError

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format
)

api_id = config.api.api_id
api_hash = config.api.api_hash
username = config.api.user
bot_token = config.bot.token

bot_client = TelegramClient('bot_client', api_id, api_hash)

user_sessions = {}

class UserSession:
    def __init__(self):
        self.current_user_entity = None
        self.selected_chat_id = None
        self.selected_chat_type = None
        self.selected_chat_title = None
        self.selected_chat_first_name = None
        self.selected_chat_last_name = None

def get_real_chat_id(chat: RequestedPeerChannel | RequestedPeerChat | RequestedPeerUser) -> int | None:
    real_chat_id: int | None = None
    try:

        if hasattr(chat, 'user_id'):
            real_chat_id = chat.user_id
        if hasattr(chat, 'chat_id'):
            real_chat_id = -chat.chat_id
        if hasattr(chat, 'channel_id'):
            real_chat_id = int(f'-100{chat.channel_id}')

        return real_chat_id
    except Exception as e:
        if isinstance(e, ValueError):
            print(f'Чат не найден: {e}')
        else:
            print(f'Ошибка при получении информации о чате: {e}')

async def authorize_user(user_id: int, bot_client: TelegramClient) -> bool:

    try:
        current_user_client = TelegramClient(user_sessions[user_id].current_user_entity.username, api_id, api_hash)

        await current_user_client.start()

        async with current_user_client:
            pass

    except Exception as e:
        print(f'Ошибка при создании клиента current_user_client: {e}')
        return False

    return False

async def delete_old_messages(user_client, chat_id, days, user_id):
    """
    Удаляет старые сообщения
    """
    sum_messages = 0
    deleted_count = 0
    error_count = 0

    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        if user_id not in user_sessions:
            await bot_client.send_message(
                user_id,
                "❌ Ошибка: пользователь не найден в списке сессий",
                buttons=Button.clear()
            )
            return

        print('=====================================================================')
        # progress_msg = await bot_client.send_message(user_id, f"⏳ Начинаю удаление сообщений старше {days} дней...")
        async for message in user_client.iter_messages(chat_id, from_user='me', offset_date=cutoff_date, limit=None):
            try:

                sum_messages += 1

                await user_client.delete_messages(chat_id, message.id, revoke=True)

                deleted_count += 1
            except Exception as e:
                error_count += 1
                logging.error(f"Ошибка при удалении сообщения: {e}")
                continue

        return sum_messages, deleted_count, error_count
    except Exception as e:
        logging.error(f"Ошибка в delete_old_messages: {e}")
        return 0, 0

async def deletion_handler(event, count_days=90):
    user_id = event.sender_id

    if user_id not in user_sessions or not user_sessions[user_id].selected_chat_id:
        await event.edit("❌ Ошибка: чат не выбран. Начните с /start", buttons=None)
        return

    chat_id = user_sessions[user_id].selected_chat_id
    chat_type = user_sessions[user_id].selected_chat_type
    chat_title = user_sessions[user_id].selected_chat_title
    chat_first_name = user_sessions[user_id].selected_chat_first_name
    chat_last_name = user_sessions[user_id].selected_chat_last_name

    chat_info = f"{chat_type} (ID {chat_id}):\n"
    if chat_type == 'User':
        if chat_last_name:
            chat_info += f"{chat_last_name} "
        else:
            chat_info += ""
        if chat_first_name:
            chat_info += f"{chat_first_name}"
        else:
            chat_info += ""
    if (chat_type == 'Small Group' or chat_type == 'Supergroup' or chat_type == 'Channel') and chat_title:
        chat_info += f"«{chat_title}»"

    confirm_buttons = [
        [
            Button.inline("✅ Да, удалить", f'confirm_{count_days}'.encode()),
            Button.inline("❌ Нет, отмена", b'cancel_confirm')
        ]
    ]

    await event.edit(
        f"⚠️ Вы уверены, что хотите удалить ВСЕ ваши сообщения старше {count_days} дней в {chat_info}?\n\n"
        "Это действие нельзя отменить!",
        buttons=confirm_buttons
    )

@bot_client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    await event.respond(LEXICON_RU["/help"], buttons=Button.clear())


@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    user_sessions[user_id] = UserSession()
    user_sessions[user_id].current_user_entity = await bot_client.get_entity(user_id)

    await authorize_user(user_id, bot_client)

    selection_buttons = bot_client.build_reply_markup(selection_button_list)
    selection_buttons.resize = True

    await event.respond(LEXICON_RU["/start"], buttons=selection_buttons)

@bot_client.on(events.Raw(types=UpdateNewMessage))
async def get_selected_chat(event):
    """
    Получает чат выбранный пользователем
    """
    message = event.message

    if not isinstance(message, MessageService):
        return

    if not hasattr(message.action, '__class__') or not isinstance(message.action, MessageActionRequestedPeerSentMe):
        return

    user_id = message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else None
    if not user_id:
        return

    await bot_client.delete_messages(message.peer_id, [message.id])

    chat = message.action.peers[0]

    if user_id not in user_sessions:
        await bot_client.send_message(
            message.peer_id,
            "❌ Ошибка: пользователь не найден в списке сессий",
            buttons=Button.clear()
        )
        return

    async with TelegramClient(user_sessions[user_id].current_user_entity.username, api_id, api_hash) as user_client:
        chat_type = None
        chat_title = None
        chat_first_name = None
        chat_last_name = None

        try:
            real_entity_id = get_real_chat_id(chat)
            real_chat = await user_client.get_entity(real_entity_id)

            if isinstance(real_chat, Chat):
                chat_type = 'Small Group'
                chat_title = real_chat.title
            if isinstance(real_chat, Channel):
                chat_title = real_chat.title
                if real_chat.megagroup or real_chat.gigagroup:
                    chat_type = 'Supergroup'
                elif real_chat.broadcast:
                    chat_type = 'Channel'
            if isinstance(real_chat, User):
                chat_type = 'User'
                chat_first_name = real_chat.first_name
                chat_last_name = real_chat.last_name
        except Exception as e:
            if isinstance(e, ValueError):
                print(f'Чат не найден: {e}')
            else:
                print(f'Ошибка при получении информации о чате: {e}')

        if user_id in user_sessions:
            user_sessions[user_id].selected_chat_id = real_entity_id
            user_sessions[user_id].selected_chat_type = chat_type
            user_sessions[user_id].selected_chat_title = chat_title
            user_sessions[user_id].selected_chat_first_name = chat_first_name
            user_sessions[user_id].selected_chat_last_name = chat_last_name

        chat_info = f"Вы выбрали {chat_type} (ID {real_entity_id}):\n"
        if chat_type == 'User':
            chat_info = f"Вы выбрали пользователя\n(ID {real_entity_id}):\n"
            if chat_last_name:
                chat_info += f"{chat_last_name} "
            else:
                chat_info += ""
            if chat_first_name:
                chat_info += f"{chat_first_name}"
            else:
                chat_info += ""
        if chat_type == 'Small Group':
            chat_info = f"Вы выбрали чат\n(ID {real_entity_id}):\n"
        if chat_type == 'Supergroup':
            chat_info = f"Вы выбрали группу\n(ID {real_entity_id}):\n"
        if chat_type == 'Channel':
            chat_info = f"Вы выбрали канал\n(ID {real_entity_id}):\n"
        if chat_title:
            chat_info += f"«{chat_title}»"

        await bot_client.send_message(
            message.peer_id,
            chat_info,
            buttons=Button.clear()
        )

        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=7)
            my_message = await user_client.get_messages(real_entity_id, from_user='me', offset_date=since_date, limit=10)
            if my_message:  # TODO: удалить после отладки
                print('COUNT MESSAGE:', len(my_message))
                print('TOTAL MESSAGE:', my_message.total)
        except Exception as e:
            if isinstance(e, ValueError):
                print(f'Чат не найден: {e}')
            else:
                print(f'Ошибка при получении информации о сообщениях в чате: {e}')

        if not len(my_message) or not my_message.total or (my_message.total == 1 and hasattr(my_message[0], 'action')):
            chat_info = f"В выбранном чате нет ваших сообщений.\nДля выбора другого чата начните заново с команды /start"
            await bot_client.send_message(
                message.peer_id,
                chat_info,
                buttons=Button.clear()
            )
            return

        await bot_client.send_message(
            entity=message.peer_id,
            message="Выберите «возраст» сообщений для удаления:",
            buttons=period_buttons
        )

@bot_client.on(events.CallbackQuery(data=b'7_days'))
async def delete_7_days(event):
    await deletion_handler(event, count_days=7)

@bot_client.on(events.CallbackQuery(data=b'30_days'))
async def delete_30_days(event):
    await deletion_handler(event, count_days=30)

@bot_client.on(events.CallbackQuery(data=b'60_days'))
async def delete_60_days(event):
    await deletion_handler(event, count_days=60)

@bot_client.on(events.CallbackQuery(data=b'90_days'))
async def delete_90_days(event):
    await deletion_handler(event, count_days=90)

@bot_client.on(events.CallbackQuery(data=b'cancel'))
async def cancel_deletion(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        chat_id = user_sessions[user_id].selected_chat_id
        chat_info = f"ID: {chat_id}"

        await event.edit(f"❌ Удаление сообщений в {chat_info} отменено.\nДля выбора другого чата\nначните с /start", buttons=None)

@bot_client.on(events.CallbackQuery(pattern=b'confirm_'))
async def confirm_deletion(event):
    try:
        days = int(event.data.decode().split('_')[1])
        user_id = event.sender_id

        if user_id not in user_sessions or not user_sessions[user_id].selected_chat_id:
            await event.edit("❌ Ошибка: чат не выбран.", buttons=None)
            return

        chat_id = user_sessions[user_id].selected_chat_id
        chat_info = f"ID: {chat_id}"

        async with TelegramClient(user_sessions[user_id].current_user_entity.username, api_id, api_hash) as user_client:

            await event.edit(f"⏳ Начинаю удаление сообщений старше {days} дней в {chat_info}...", buttons=None)
            sum_messages, deleted_count, error_count = await delete_old_messages(user_client, chat_id, days, user_id)

        result_message = (
            f"✅ Удаление завершено!\n"
            f"• Сообщений старше {days} дней: {sum_messages}\n"
            f"• Удалено сообщений: {deleted_count}\n"
            f"• Ошибок при удалении: {error_count}\n"
            f"• Чат: {chat_info}\n"
        )

        await event.respond(result_message)

    except Exception as e:
        logging.error(f"Ошибка при подтверждении удаления: {e}")
        await event.edit("❌ Произошла ошибка при удалении сообщений.", buttons=None)

@bot_client.on(events.CallbackQuery(data=b'cancel_confirm'))
async def cancel_confirm(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        chat_id = user_sessions[user_id].selected_chat_id
        chat_info = f"ID: {chat_id}"

        await event.edit(f"❌ Удаление сообщений в {chat_info} отменено.", buttons=None)

bot_client.start(bot_token=bot_token)
bot_client.run_until_disconnected()
