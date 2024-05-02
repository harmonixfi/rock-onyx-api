import asyncio
import logging
import traceback
from typing import Optional

from web3 import AsyncWeb3, Web3, WebsocketProviderV2
from web3.providers.websocket.websocket_connection import WebsocketConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


class WebSocketManager:
    def __init__(self, url, logger=None):
        self.url = url
        self.w3_socket = None
        self.websocket: Optional[WebsocketConnection] = None
        self.logger = logging.getLogger(__name__) if logger is None else logger

    async def connect(self):
        self.w3_socket = Web3(Web3.WebsocketProvider(self.url))
        self.w3 = await AsyncWeb3.persistent_websocket(WebsocketProviderV2(self.url))
        await self.w3.provider.connect()
        self.websocket = self.w3.ws

    async def disconnect(self):
        if self.websocket:
            await self.w3.provider.disconnect()
            self.websocket = None

    async def reconnect(self):
        self.logger.info("Reconnecting to websocket provider")
        await self.disconnect()
        await self.connect()

    async def read_messages(self, read_timeout=0.1, backoff=0.1, on_disconnect=None):
        while True:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(), timeout=read_timeout
                )
                yield message
            except ConnectionClosedError as e:
                if on_disconnect:
                    on_disconnect()
                self.logger.error("Websocket connection close")
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
                await self.reconnect()
            except ConnectionClosedOK as e:
                if on_disconnect:
                    on_disconnect()
                self.logger.error("Websocket connection close")
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
                await self.reconnect()
            except asyncio.TimeoutError:
                await asyncio.sleep(backoff)
            except Exception as e:
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
                await asyncio.sleep(1)
