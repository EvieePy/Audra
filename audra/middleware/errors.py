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

import http
import logging
from typing import Any

from ..exceptions import BaseHTTPException
from ..types_ import Message, Receive, Scope, Send
from .base import Middleware


LOGGER: logging.Logger = logging.getLogger(__name__)


__all__ = ("ExceptionMiddleware",)


CSS = """
html, body {
    margin: 0;
    box-sizing: border-box;
    font-family: Arial;
}

a {
    color: khaki;
    text-decoration: none;
}

h2 {
    margin-bottom: 0;
}

.header {
    display: flex;
    flex-direction: column;
    background-color: #4e4c6f;
    padding: 1rem;
    color: #fff;
    font-size: 0.9em;
    &>h5 {
        margin-top: 0;
    }
    gap: 0.5rem;
}
"""

HTML = """
<html>
    <head>
    <style>
        {STYLES}
    </style>
    </head>
    <body>

        <main>
            <div class="header">
                <h2>{STATUS} - <a href={STATUS_URL} target="_blank">{ERROR}</a></h2>
                <h5>{ERROR_DESC}</h5>
            </div>
        </main>

    </body>
</html>
"""


MDN_STATUS_URL: str = "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/"


class ExceptionMiddleware(Middleware):
    def __init__(self, *, debug: bool = False) -> None:
        self.debug = debug

    async def test(self, scope: Scope, receive: Receive, send: Send, *, error: Exception | BaseHTTPException) -> None:
        from ..enums import SendEvent

        status = error.status if isinstance(error, BaseHTTPException) else 500
        details = error.details if isinstance(error, BaseHTTPException) else "Internal Server Error"
        url = MDN_STATUS_URL + str(status)

        desc = http.HTTPStatus(status).description
        headers = [(b"content-type", b"text/html"), (b"content-disposition", b"inline")]
        html = HTML.format(STATUS=status, ERROR=details, ERROR_DESC=desc, STYLES=CSS, STATUS_URL=url)

        await send({"type": SendEvent.HTTPResponseStart.value, "status": status, "headers": headers})
        await send({"type": SendEvent.HTTPResponseBody.value, "body": html.encode()})

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
        except Exception as e:
            await self.test(scope, receive, send_, error=e)
