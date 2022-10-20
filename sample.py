# -*- coding: utf-8 -*-
import argparse
import asyncio
import logging
import os
from typing import Awaitable, Callable, Optional
from rich.logging import RichHandler


import blivedm

# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    12235923,
    14327465,
    21396545,
    21449083,
    23105590,
]
LOG_ROOT = "./log"


async def main(ids: list[int]):
    """
    同时监听多个直播间
    """
    clients = [blivedm.BLiveClient(room_id) for room_id in ids]
    handler = MyHandler()
    for client in clients:
        client.add_handler(handler)
        client.start()

    try:
        await asyncio.gather(*(client.join() for client in clients))
    finally:
        await asyncio.gather(*(client.stop_and_close() for client in clients))


class MyHandler(blivedm.BaseHandler):
    # 演示如何添加自定义回调
    _CMD_CALLBACK_DICT: dict[
        str, Optional[Callable[["MyHandler", blivedm.BLiveClient, dict], Awaitable]]
    ] = {k: v for (k, v) in blivedm.BaseHandler._CMD_CALLBACK_DICT.items()}

    # # 入场消息回调
    # async def __on_interact_word(self, client: blivedm.BLiveClient, command: dict):
    #     traffic_logger.debug(
    #         "[Room ID]: %d - [Enter room]: %s", client.room_id, command["data"]["uname"]
    #     )

    # # _CMD_CALLBACK_DICT["INTERACT_WORD"] = __on_interact_word

    async def __on_watch_change(self, client: blivedm.BLiveClient, command: dict):
        traffic_logger.info(
            "[Room ID]: %d - [Watches]: %d", client.room_id, command["data"]["num"]
        )

    async def __on_like_info_update(self, client: blivedm.BLiveClient, command: dict):
        traffic_logger.info(
            "[Room ID]: %d - [Likes]: %d",
            client.room_id,
            command["data"]["click_count"],
        )

    _CMD_CALLBACK_DICT["WATCHED_CHANGE"] = __on_watch_change
    _CMD_CALLBACK_DICT["LIKE_INFO_V3_UPDATE"] = __on_like_info_update

    async def _on_heartbeat(
        self, client: blivedm.BLiveClient, message: blivedm.HeartbeatMessage
    ):
        traffic_logger.debug(
            "[Room ID]: %d - [Popularity]: %d", client.room_id, message.popularity
        )

    async def _on_danmaku(
        self, client: blivedm.BLiveClient, message: blivedm.DanmakuMessage
    ):
        dm_logger.info(
            "[Room ID]: %d - [User]: '%s' - [Chat]: '%s'",
            client.room_id,
            message.uname,
            message.msg,
        )

    async def _on_gift(self, client: blivedm.BLiveClient, message: blivedm.GiftMessage):
        gift_logger.info(
            "[Room ID]: %d - [User]: '%s' - [Gift]: '%s' - [Number]: %d - [Value]: %d '%s'",
            client.room_id,
            message.uname,
            message.gift_name,
            message.num,
            message.total_coin,
            message.coin_type,
        )

    async def _on_buy_guard(
        self, client: blivedm.BLiveClient, message: blivedm.GuardBuyMessage
    ):
        gift_logger.info(
            "[Room ID]: %d - [User]: '%s' - [Guard]: '%s'",
            client.room_id,
            message.username,
            message.gift_name,
        )

    async def _on_super_chat(
        self, client: blivedm.BLiveClient, message: blivedm.SuperChatMessage
    ):
        dm_logger.info(
            "[Room ID]: %d - [User]: '%s' - [Super chat]: '%s'",
            client.room_id,
            message.uname,
            message.message,
        )


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-i",
        "--id",
        nargs="+",
        type=int,
        help="直播间ID，可以指定多个，如果不指定则使用默认值",
        default=TEST_ROOM_IDS,
    )
    argparser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="删除已存在的log文件",
    )
    args = argparser.parse_args()

    if args.delete:
        os.system(f"rm {LOG_ROOT}/*")

    stdout_handler = RichHandler(show_path=False, show_level=False)

    cmd_log_handler = logging.FileHandler("./log/cmd.log")
    cmd_log_handler.setFormatter(
        logging.Formatter("[%(asctime)s] - [%(levelname)s] - %(message)s")
    )
    cmd_logger = logging.getLogger("blivedm.cmd")
    cmd_logger.setLevel(logging.DEBUG)
    # cmd_logger.addHandler(stdout_handler)
    cmd_logger.addHandler(cmd_log_handler)

    dm_log_handler = logging.FileHandler(os.path.join(LOG_ROOT, "dm.log"))
    dm_log_handler.setFormatter(logging.Formatter("[%(asctime)s] - %(message)s"))
    dm_logger = logging.getLogger("blivedm.dm")
    dm_logger.setLevel(logging.DEBUG)
    dm_logger.addHandler(stdout_handler)
    dm_logger.addHandler(dm_log_handler)

    traffic_log_handler = logging.FileHandler(os.path.join(LOG_ROOT, "traffic.log"))
    traffic_log_handler.setFormatter(
        logging.Formatter("[%(asctime)s] - [%(levelname)s] - %(message)s")
    )
    traffic_logger = logging.getLogger("blivedm.traffic")
    traffic_logger.setLevel(logging.DEBUG)
    # traffic_logger.addHandler(stdout_handler)
    traffic_logger.addHandler(traffic_log_handler)

    gift_log_handler = logging.FileHandler(os.path.join(LOG_ROOT, "gift.log"))
    gift_log_handler.setFormatter(logging.Formatter("[%(asctime)s] - %(message)s"))
    gift_logger = logging.getLogger("blivedm.gift")
    gift_logger.setLevel(logging.DEBUG)
    # gift_logger.addHandler(stdout_handler)
    gift_logger.addHandler(gift_log_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(args.id))
