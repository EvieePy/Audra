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

from .enums import SendEvent
from .middleware.base import Middleware


__all__ = ("Route", "Router")


class Route: ...


class Router(Middleware):
    async def __call__(self, scope: ..., receive: ..., send: ...) -> ...:
        await send({"type": SendEvent.HTTPResponseStart.value, "status": 200})
        await send({"type": SendEvent.HTTPResponseBody.value, "body": b"Hello World!"})
