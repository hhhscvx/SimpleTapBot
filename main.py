import asyncio
import os

from pyrogram import Client

from data import config
from utils.simplecoin import SimpleCoin
from utils.core.telegram import Accounts


async def main():
    # await Accounts().create_sessions()
    accounts = await Accounts().get_accounts()

    for account in accounts:
        session_name, phone_number, proxy = account.values()
        client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            phone_number=phone_number,
            workdir=config.WORKDIR
        )
        simplecoin = SimpleCoin(tg_client=client)
        await simplecoin.get_tg_web_data()


if __name__ == "__main__":
    if not os.path.exists('sessions'):
        os.mkdir('sessions')
    if not os.path.exists('sessions/accounts.json'):
        with open("sessions/accounts.json", 'w') as f:
            f.write("[]")
    asyncio.run(main())
