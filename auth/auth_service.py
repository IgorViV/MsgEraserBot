# Модуль авторизации
import os
import logging
from config.config import Config, load_config
from telethon import TelegramClient

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format
)

logger = logging.getLogger(__name__)

async def is_authorized(client: TelegramClient) -> bool:
    """ Проверка авторизации в Telegram """

    try:
        await client.connect()

        if await client.is_user_authorized():
            await client.disconnect()
            return True
        else:
            await client.disconnect()
            return False

    except Exception as e:
        logger.error(f"Ошибка проверки авторизации: {str(e)}")
        await client.disconnect()
        return False
