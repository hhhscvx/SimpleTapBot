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
from utils.core import logger, ProfileResult


class SimpleCoin:
    def __init__(self, tg_client: Client, proxy: str | None = None) -> None:
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.proxy = f"{config.PROXY_TYPE_REQUESTS}://{proxy}" if proxy else None
        connector = ProxyConnector.from_url(url=self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)
        self.msg_was_send = False

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

    async def profile(self) -> ProfileResult:
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/profile/",
                                       json=await self._get_json_data())
        resp_json = await resp.json()
        await asyncio.sleep(1)
        data = resp_json.get('data')

        return ProfileResult(
            balance=data.get('balance'),
            active_farming_balance=data.get('activeFarmingBalance'),
            active_farming_seconds=data.get('activeFarmingSeconds'),
            max_farming_seconds=data.get('maxFarmingSecondSec'),
            available_taps=data.get('availableTaps'),  # буду тапать когда available taps меньше чем max
            max_available_taps=data.get('maxAvailableTaps'),
            tap_size=data.get('tapSize'),
            spin_count=data.get('spinCount')  # fortune
        )

    async def claim(self) -> dict:
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/claim/",
                                       json=await self._get_json_data())
        return await resp.json()

    async def start(self) -> dict:
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/activate/",
                                       json=await self._get_json_data())
        return await resp.json()

    async def tap(self, taps_count: int) -> dict:
        json_data = await self._get_json_data()
        json_data['count'] = taps_count
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/tap/",
                                       json=json_data)
        return await resp.json()  # result, message: OK

    async def get_tasks(self) -> list[dict]:
        json_data = await self._get_json_data()
        json_data['lang'] = "en"
        json_data['platform'] = 1
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/get-task-list-2/",
                                       json=json_data)
        resp_json = await resp.json()
        return resp_json['data']['social']

    async def start_task(self, task_id: int, task_type: int) -> int:
        """Там никакой проверки нет и всегда возвращается 200, так что просто каждой таске отправлять start и check"""
        json_data = await self._get_json_data()
        json_data['id'] = task_id
        json_data['type'] = task_type
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/start-task-start-2/",
                                       json=json_data)
        return resp.status

    async def check_task(self, task_id: int, task_type: int) -> int:
        json_data = await self._get_json_data()
        json_data['id'] = task_id
        json_data['type'] = task_type
        resp = await self.session.post("https://api.thesimpletap.app/api/v1/public/telegram/start-task-start-2/",
                                       json=json_data)
        return resp.status

    async def _get_json_data(self) -> dict[str, str | int]:
        return {
            'authData': await self.get_tg_web_data(),
            'userId': await self.get_user_tg_id()
        }

    async def get_user_tg_id(self) -> int:
        await self.tg_client.connect()
        user_tg_id = (await self.tg_client.get_me()).id
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

            if self.msg_was_send is False:
                await self.tg_client.send_message('Simple_Tap_Bot', '/start')
                self.msg_was_send = True
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
