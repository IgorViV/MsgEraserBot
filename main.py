import logging
from telethon import TelegramClient, events
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


@bot_client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    await event.respond(LEXICON_RU["/help"], buttons=None)


@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    if not event.is_private:
        return

    user_id = event.sender_id

    selection_buttons = bot_client.build_reply_markup(selection_button_list)
    selection_buttons.resize = True

    await event.respond(LEXICON_RU["/start"], buttons=selection_buttons)


bot_client.start(bot_token=bot_token)
user_client.start()
bot_client.run_until_disconnected()
