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

from typing import Any

from .enums import SendEvent
from .types_ import Receive, Scope, Send


class TestResponse:
    def __init__(self, body: str | None = None, status: int = 200) -> None:
        self.body = body
        self.status = status

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Any:
        await send({"type": SendEvent.HTTPResponseStart.value, "status": self.status})
        await send({"type": SendEvent.HTTPResponseBody.value, "body": self.body.encode() if self.body else b""})
