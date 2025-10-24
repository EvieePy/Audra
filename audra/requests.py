"""Copyright © 2025, EvieePy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .exceptions import ClientDisconnected
from .headers import FrozenHeaders


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from .application import Audra
    from .state import State
    from .types_ import HTTPMethod, HTTPScope, Message, Receive, Send, WebsocketScope


__all__ = ("Request",)


class BaseRequest:
    def __init__(self, scope: HTTPScope | WebsocketScope, receive: Receive, send: Send) -> None:
        self._scope = scope
        self._receive = receive
        self._send = send

        self._headers = FrozenHeaders(self._scope["headers"])

    @property
    def scope(self) -> HTTPScope | WebsocketScope:
        return self._scope

    @property
    def state(self) -> State: ...

    @property
    def headers(self) -> FrozenHeaders:
        return self._headers

    @property
    def app(self) -> Audra | None:
        return self._scope.get("app")


class Request(BaseRequest):
    def __init__(self, scope: HTTPScope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self._scope = scope

        self._fetched: bool = False
        self._disconnected: bool = False
        self._body = b""

    @property
    def method(self) -> HTTPMethod:
        return self._scope["method"]

    async def body(self) -> bytes:
        if self._fetched:
            return self._body

        async for _ in self.stream(memorize=True):
            pass

        return self._body

    async def text(self) -> str:
        if not self._fetched:
            await self.body()

        return self._body.decode()

    async def stream(self, memorize: bool = False) -> AsyncGenerator[bytes, None]:
        if self._fetched:
            yield self._body
            yield b""

        while not self._fetched:
            message: Message = await self._receive()

            if message["type"] == "http.disconnect":
                self._disconnected = True
                raise ClientDisconnected

            elif message["type"] != "http.request":
                continue

            body = message.get("body", b"")
            more: bool = message.get("more_body", False)

            if body:
                if memorize:
                    self._body += body
                yield body

            if not more:
                self._fetched = True

        yield b""

    async def json(self, *, serializer: Callable[[bytes], dict[str, Any]] | None = None) -> dict[str, Any]:
        app = self._scope.get("app")
        serial_ = serializer or app._serializer if app else json.loads

        if not self._fetched:
            await self.body()

        return serial_(self._body)

    async def form(self) -> ...: ...
