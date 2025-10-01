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

from __future__ import annotations

from typing import Any

from ..types_ import ASGIApp


__all__ = ("ASGIMiddleware", "Middleware")


class ASGIMiddleware(ASGIApp):
    app: ASGIApp


class Middleware(ASGIApp):
    app: ASGIApp

    __has_loaded__: bool = False

    async def __call__(self, scope: ..., receive: ..., send: ...) -> Any: ...

    async def on_load(self) -> None: ...

    @property
    def next(self) -> ASGIApp:
        return self.app
