
from asyncio import sleep
from random import randint, uniform

from pyrogram import Client

from data import config
from utils.core import logger
from utils.simplecoin import SimpleCoin


async def start(tg_client: Client, proxy: str | None = None):
    simplecoin = SimpleCoin(tg_client=tg_client, proxy=proxy)
    session_name = tg_client.name + '.session'

    await sleep(uniform(*config.DELAY_CONN_ACCOUNT))

    tasks_completed = False

    while True:
        try:
            # Claim | Farm
            profile = await simplecoin.profile()
            logger.success(f"{session_name} | Signed in | Balance: {profile.balance} SMPL")
            await sleep(1)
            if profile.active_farming_seconds == profile.max_farming_seconds:
                claim = await simplecoin.claim()
                if claim['result'] == "OK":
                    logger.success(f"{session_name} | Claimed {profile.active_farming_balance} SMPL!")
                    await sleep(uniform(0.75, 1.5))
                    start_farming = await simplecoin.start()
                    if start_farming['result'] == "OK":
                        logger.success(f"{session_name} | Start farming!")
            else:
                logger.info(
                    f"{session_name} | Already farming ({profile.active_farming_seconds}/{profile.max_farming_seconds}s)")

            # Tasks
            if tasks_completed is False and config.DO_TASKS is True:
                tasks = await simplecoin.get_tasks()
                for task in tasks:
                    await simplecoin.start_task(task_id=task['id'], task_type=task['type'])
                    await sleep(1)
                    task_id = task['id']
                    if await simplecoin.check_task(task_id=task_id, task_type=task['type']) == 200:
                        logger.success(
                            f"{session_name} | Check task {task['title'] if task['title'].strip() != '' else f'№{task_id}'}")
                    await sleep(uniform(2, 3))
                tasks_completed = True

            # Taps
            profile = await simplecoin.profile()
            available_taps = profile.available_taps
            while True:
                if available_taps > config.MIN_AVAILABLE_TAPS:
                    taps_count = randint(*config.RANDOM_TAPS_COUNT) * profile.tap_size
                    tap = await simplecoin.tap(taps_count=taps_count)
                    if tap['result'] == "OK":
                        logger.success(f"{session_name} | Tapped +{taps_count} SMPL!")
                        available_taps -= taps_count
                    await sleep(uniform(*config.SLEEP_BETWEEN_TAP))
                else:
                    profile = await simplecoin.profile()
                    sleep_time = uniform(*config.SLEEP_BY_MIN_ENERGY)
                    logger.info(
                        f"{session_name} | Energy: {profile.available_taps}/{profile.max_available_taps} | Balance: {int(profile.balance)} SMPL")
                    logger.info(f" | Sleep {int(sleep_time)}s...")
                    await sleep(sleep_time)
                    break

        except Exception as err:
            logger.error(f"{session_name} | Unknown Error: {err}")
            await sleep(delay=3)
