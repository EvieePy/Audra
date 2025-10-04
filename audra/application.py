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

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self

from .enums import ReceiveEvent, SendEvent
from .exceptions import *
from .middleware import ASGIMiddleware, ExceptionMiddleware, Middleware
from .routes import RouterMiddleware


if TYPE_CHECKING:
    from collections.abc import Callable

    from types_ import (
        ASGIApp,
        HTTPScope,
        LifespanCallbackT,
        LifespanMessageT,
        LifespanScope,
        Receive,
        ReceiveLS,
        Scope,
        Send,
        State,
    )


__all__ = ("Audra", "lifespan")


LOGGER: logging.Logger = logging.getLogger(__name__)


class lifespan:  # Reason: Decorator class...
    _injected: Audra | None = None

    def __init__(self, coro: LifespanCallbackT, /, *, type_: Literal["startup", "shutdown", "special"]) -> None:
        self.type_: Literal["startup", "shutdown", "special"] = type_
        self._coro = coro

    async def __call__(self, state: State | None) -> None:
        coro = self._coro(self._injected, state) if self._injected else self._coro(state)  # type: ignore
        await coro

    async def __aenter__(self) -> Self:
        return self

    @classmethod
    def startup(cls) -> Callable[[LifespanCallbackT], Self]:
        def decorator(cb: LifespanCallbackT) -> Self:
            return cls(cb, type_="startup")

        return decorator

    @classmethod
    def shutdown(cls) -> Callable[[LifespanCallbackT], Self]:
        def decorator(cb: LifespanCallbackT) -> Self:
            return cls(cb, type_="shutdown")

        return decorator

    @classmethod
    def _special(cls) -> Callable[[LifespanCallbackT], Self]:
        def decorator(cb: LifespanCallbackT) -> Self:
            return cls(cb, type_="special")

        return decorator


class Audra:
    __lifespans__: ClassVar[dict[Literal["startup", "shutdown"], list[lifespan]]] = {"startup": [], "shutdown": []}
    __middleware__: ClassVar[list[Middleware | ASGIMiddleware]] = []
    __stack__: ASGIApp | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        inst = super().__new__(cls)

        for base in reversed(cls.__mro__):
            for _, meth in base.__dict__.items():  # noqa: PERF102 [Reason: Possibly needed later...]
                if isinstance(meth, lifespan):
                    if meth.type_ == "special":
                        continue

                    meth._injected = inst
                    inst.__lifespans__[meth.type_].append(meth)

        inst._startup._injected = inst
        inst.__lifespans__["startup"].insert(0, inst._startup)

        return inst

    def __init__(
        self, *, build_on_startup: bool = True, middleware: list[Middleware | ASGIMiddleware] | None = None
    ) -> None:
        self._router: RouterMiddleware = RouterMiddleware()
        self._build_on_startup = build_on_startup
        self._user_middleware = middleware or []

    async def __call__(self, scope: Scope, receive: Receive | ReceiveLS, send: Send) -> Any:
        if scope["type"] == "lifespan":
            await self._lifespan_handler(scope, receive, send)  # type: ignore
        elif scope["type"] == "http":
            await self._handle_http(scope, receive, send)  # type: ignore
        elif scope["type"] == "websocket":
            ...

    async def _build_middleware(self) -> ASGIApp:
        middlewares = [ExceptionMiddleware(), *self.__middleware__, *self._user_middleware]
        prev = self._router

        for m in reversed(middlewares):
            m.app = prev

            if isinstance(m, Middleware) and not m.__has_loaded__:
                try:
                    await m.on_load()
                    m.__has_loaded__ = True
                except Exception as e:
                    raise MiddlewareLoadException(f"The Middleware {prev!r} failed to load.") from e

            prev = m

        return prev

    async def _handle_http(self, scope: HTTPScope, receive: Receive, send: Send) -> None:
        if not self.__stack__:
            self.__stack__ = await self._build_middleware()

        await self.__stack__(scope, receive, send)

    @lifespan._special()
    async def _startup(self, state: State) -> None:
        if self._build_on_startup and not self.__stack__:
            self.__stack__ = await self._build_middleware()

    async def _lifespan_handler(self, scope: LifespanScope, receive: ReceiveLS, send: Send) -> None:
        startup_e: str | None = None
        shutdown_e: str | None = None

        while True:
            message: LifespanMessageT = await receive()
            state: State | None = scope.get("state")
            received = ReceiveEvent(message["type"])

            if received is ReceiveEvent.LSStartup:
                for handler in self.__lifespans__["startup"]:
                    try:
                        await handler(state)
                    except Exception as e:
                        startup_e = (
                            f"An error in the 'lifespan.startup' handler {handler!r} prevented {self!r} from starting: {e}"
                        )

                        LOGGER.critical(startup_e, exc_info=e)
                        await send({"type": SendEvent.LSStartupFailed.value, "message": startup_e})
                        return

                await send({"type": SendEvent.LSStartupComplete.value})

            elif received is ReceiveEvent.LSShutdown:
                for handler in self.__lifespans__["shutdown"]:
                    try:
                        await handler(state)
                    except Exception as e:
                        shutdown_e = (
                            f"An error in the 'lifespan.shutdown' handler {handler!r} prevented {self!r} "
                            f"from closing gracefully: {e}"
                        )

                        LOGGER.critical(shutdown_e, exc_info=e)
                        await send({"type": SendEvent.LSShutdownFailed.value, "message": shutdown_e})
                        return

                await send({"type": SendEvent.LSShutdownComplete.value})
                break
