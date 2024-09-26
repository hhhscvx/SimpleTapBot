
from asyncio import sleep
from random import uniform

from pyrogram import Client

from data import config
from utils.simplecoin import SimpleCoin


async def start(tg_client: Client, proxy: str | None = None):
    simplecoin = SimpleCoin(tg_client=tg_client, proxy=proxy)
    session_name = tg_client.name + '.session'

    await sleep(uniform(*config.DELAY_CONN_ACCOUNT))

    while True:
        try:
            ...

        except Exception as error:
            ...
