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

from collections.abc import Sequence
from typing import Any

from .enums import SendEvent
from .headers import Headers
from .types_ import Receive, Scope, Send
from .utils import MISSING


__all__ = ("EmptyResponse", "HTMLResponse", "PlainTextResponse", "Response")


type BytesOrStr = bytes | str
type HeadersT = dict[str, BytesOrStr] | Headers | Sequence[tuple[bytes | str, bytes | str]]


class _BaseResponse:
    media_type: str | None = None
    charset: str = "utf-8"

    def __init__(self, body: Any | None = None, *, status: int = 200, headers: HeadersT | None = None) -> None:
        self.body = self.encode(body)
        self.status = status
        self._headers = self._process_headers(headers)

    def _process_headers(self, headers: HeadersT | None) -> Headers:
        compiled: Headers

        if isinstance(headers, Headers):
            compiled = headers
        elif headers is None:
            compiled = Headers()
        else:
            compiled = Headers(headers)

        set_cl = compiled.get("content-length", MISSING)
        set_ct = compiled.get("content-type", MISSING)

        if set_cl is MISSING and self.status >= 200 and self.status not in (204, 304):
            compiled["content-length"] = str(len(self.body))

        media_type = self.media_type
        if not media_type or set_ct is not MISSING:
            return compiled

        compiled["content-type"] = media_type
        if media_type.startswith("text/") and "charset=" not in media_type.lower():
            compiled.append_to_field("content-type", f"charset={self.charset}", separator=";")

        return compiled

    def encode(self, body: Any) -> bytes | memoryview:
        if body is None:
            return b""

        if isinstance(body, (bytes, memoryview)):
            return body  # type: ignore

        return bytes(body, encoding=self.charset)

    @property
    def headers(self) -> Headers:
        return self._headers

    @headers.setter
    def headers(self, other: HeadersT | None) -> None:
        self._headers = self._process_headers(other)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Any:
        await send({"type": SendEvent.HTTPResponseStart.value, "status": self.status, "headers": self.headers.raw()})
        await send({"type": SendEvent.HTTPResponseBody.value, "body": self.body})


class Response(_BaseResponse): ...


class EmptyResponse(Response):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(None, status=204)


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"
