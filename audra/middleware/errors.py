"""Copyright 2025 EvieePy

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

from typing import Any

from ..types_ import Message, Receive, Scope, Send
from .base import Middleware


__all__ = ("ExceptionMiddleware",)


class ExceptionMiddleware(Middleware):
    def __init__(self, *, debug: bool = False) -> None:
        self.debug = debug

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Any:
        if scope["type"] != "http":
            await self.next(scope, receive, send)
            return

        started = False

        async def send_(message: Message) -> None:
            nonlocal started

            if message["type"] == "http.response.start":
                started = True

            await send(message)

        try:
            await self.next(scope, receive, send_)
        except Exception:
            ...
