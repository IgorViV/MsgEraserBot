import asyncio
import logging
from telethon.sync import TelegramClient, events
from config.config import Config, load_config

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format
)

api_id = config.api.api_id
api_hash = config.api.api_hash
username = config.api.user

with TelegramClient(username, api_id, api_hash) as client:
   client.send_message('me', 'Hello, myself!')
   print(client.download_profile_photo('me'))

   @client.on(events.NewMessage(pattern='(?i).*Hello'))
   async def handler(event):
      await event.reply('Hey!')

   client.run_until_disconnected()
