from dataclasses import dataclass
from environs import Env

@dataclass
class TgBot:
    token: str
    admin_ids: list[int]

@dataclass
class ApiConfig:
    api_id: int
    api_hash: str
    user: str

@dataclass
class LogSettings:
    level: str
    format: str

@dataclass
class Config:
    bot: TgBot
    api: ApiConfig
    log: LogSettings

def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMIN_IDS')))
        ),
        api=ApiConfig(
            api_id=env('API_ID'),
            api_hash=env('API_HASH'),
            user=env('USERNAME')
        ),
        log=LogSettings(
            level=env('LOG_LEVEL'),
            format=env('LOG_FORMAT')
        )
    )
