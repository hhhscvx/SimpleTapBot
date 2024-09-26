import asyncio
from random import choices, randint, uniform
import string
from urllib.parse import quote, unquote

import aiohttp
from aiohttp_socks import ProxyConnector
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
from pyrogram.raw.types import WebViewResultUrl
from fake_useragent import UserAgent
from faker import Faker

from data import config
from utils.core import logger


class SimpleCoin:
    def __init__(self, tg_client: Client, proxy: str | None = None) -> None:
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.proxy = f"{config.PROXY_TYPE_REQUESTS}://{proxy}" if proxy else None
        connector = ProxyConnector.from_url(url=self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        if proxy:
            proxy = {
                "scheme": config.PROXY_TYPE_TG,
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        headers = {"User-Agent": UserAgent(os='android').random}
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def logout(self) -> None:
        await self.session.close()

    async def balance(self) -> tuple[float, int]:
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/profile/",
                                       json=await self._get_json_data())
        resp_json = await resp.json()
        await asyncio.sleep(1)

        active_farming_balance = resp_json.get('activeFarmingBalance')
        active_farming_seconds = resp_json.get('activeFarmingSeconds')
        return active_farming_balance, active_farming_seconds

    async def claim(self) -> dict:
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/claim/",
                                       json=await self._get_json_data())
        resp_json = await resp.json()

        return resp_json()

    async def _get_json_data(self) -> dict[str, str | int]:
        return {
            'authData': await self.get_tg_web_data(),
            'userId': await self.get_user_tg_id()
        }

    async def get_user_tg_id(self) -> int:
        await self.tg_client.connect()
        user_tg_id = (await self.tg_client.get_me()).id
        print(f'user_tg_id: {user_tg_id} | Type: {type(user_tg_id)}')
        await self.tg_client.disconnect()
        return user_tg_id

    async def get_tg_web_data(self) -> str | None:
        try:
            await self.tg_client.connect()

            if not (await self.tg_client.get_me()).username:
                while True:
                    username = Faker(locale='en_US').name().replace(" ", "") + '_' + \
                        ''.join(choices(string.digits, k=randint(3, 6)))
                    if await self.tg_client.set_username(username):
                        logger.success(f"{self.session_name} | Set username @{username}")
                        break
                await asyncio.sleep(5)

            await self.tg_client.send_message('Simple_Tap_Bot', '/start')
            await asyncio.sleep(uniform(1.5, 2))

            web_view: WebViewResultUrl = await self.tg_client.invoke(RequestWebView(
                peer=await self.tg_client.resolve_peer('Simple_Tap_Bot'),
                bot=await self.tg_client.resolve_peer('Simple_Tap_Bot'),
                platform='android',
                from_bot_menu=False,
                url="https://simpletap.app/"
            ))
            await self.tg_client.disconnect()
            auth_url = web_view.url

            query = unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            query_id = query.split('query_id=')[1].split('&user=')[0]
            user = quote(query.split("&user=")[1].split('&auth_date=')[0])
            auth_date = query.split('&auth_date=')[1].split('&hash=')[0]
            hash_ = query.split('&hash=')[1]

            return f"query_id={query_id}&user={user}&auth_date={auth_date}&hash={hash_}"

        except Exception as err:
            raise err
            return
