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

from typing import TYPE_CHECKING, Any, Self

from .exceptions import HTTPMethodNotAllowed, HTTPNotFound, HTTPNotImplemented, MiddlewareLoadException, RouteAlreadyExists
from .middleware.base import ASGIMiddleware, Middleware
from .responses import TestResponse
from .types_ import Callable, HTTPMethod, Receive, RouteCallbackT, Scope, Send
from .utils import get_route_path


if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ("Route", "Router", "route")


type DecoRoute = Callable[[RouteCallbackT | Route], Route]


# NOTE: TESTING
class TestReq:
    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send


class Route(Middleware):
    __route_name__: str

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        inst = super().__new__(cls)
        name = kwargs.get("name", args[0].__name__)
        inst.__route_name__ = name

        return inst

    def __init__(
        self,
        coro: RouteCallbackT,
        *,
        path: str,
        methods: list[HTTPMethod],
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
    ) -> None:
        methods = [m.upper() for m in methods]  # type: ignore [Reason: Type-Checker doesn't understand safety]
        if "GET" in methods:
            methods.append("HEAD")

        self._methods: set[HTTPMethod] = set(methods)
        self._middleware: list[Middleware | ASGIMiddleware] = list(middleware) if middleware else []
        self._path = path
        self._coro = coro

    def match(self, path: str, method: HTTPMethod) -> bool | None:
        # True: Full Match
        # False: No Match
        # None: Partial Match (E.g. Path matches but method isn't allowed)

        # First case can shortcut and doesn't need to do any parameter matching...
        if path == self._path:
            return True if method in self._methods else None

    async def _build_middleware(self) -> None:
        prev = self

        for m in reversed(self._middleware):
            if isinstance(m, Middleware) and not m.__has_loaded__:
                try:
                    await m.on_load()
                    m.__has_loaded__ = True
                except Exception as e:
                    raise MiddlewareLoadException(f"The Middleware {prev!r} failed to load on route {self!r}.") from e

            m.app = prev
            prev = m

        self.app = prev
        self.__has_loaded__ = True

    async def on_load(self) -> None:
        await self._build_middleware()

    async def invoke(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            raise HTTPNotImplemented

        if not self.__has_loaded__:
            await self._build_middleware()

        method = scope["method"]
        if method not in self._methods:
            raise HTTPMethodNotAllowed

        await self.app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # NOTE: TESTING
        req = TestReq(scope, receive, send)
        resp = await self._coro(req)

        if resp:
            await resp(scope, receive, send)
        else:
            await (TestResponse(status=204))(scope, receive, send)


class Router(Middleware):
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add_route(self, route: Route) -> None:
        # TODO: Check for duplicates...
        self._routes.append(route)

    def resolve_path(self, path: str) -> Route | None:
        for route in self._routes:
            ...

    def find_route(self, scope: Scope) -> Route | None:
        assert scope["type"] == "http"

        path: str = get_route_path(scope)
        route = self.resolve_path(path)

        return route

    # NOTE: Testing...
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return

        route_ = self.find_route(scope)
        print(route_)

        if not route_:
            raise HTTPNotFound

        await route_.invoke(scope, receive, send)


class _RouteDecoMeta(type):
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        # Prevent __init__ and allow __call__ to be called as a classmethod
        return cls.__call__(*args, **kwargs)


class route(metaclass=_RouteDecoMeta):  # reason: class decorator...
    @classmethod
    def __call__(
        cls: type[route],
        path: str,
        *,
        methods: list[HTTPMethod] = ["GET"],
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=methods, middleware=middleware)

        return wrapper

    @classmethod
    def _wrapper(
        cls: type[route],
        func: RouteCallbackT | Route,
        *,
        path: str,
        methods: list[HTTPMethod],
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
    ) -> Route:
        if isinstance(func, Route):
            raise RouteAlreadyExists(
                f"{func.__route_name__!r} is already a Route. "
                f"Consider using the '@route(path='{path}', methods=[...])' decorator to pass multiple methods instead."
            )

        return Route(func, path=path, methods=methods, middleware=middleware)

    @classmethod
    def get(cls: type[route], path: str, *, middleware: Sequence[Middleware | ASGIMiddleware] | None = None) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["GET"], middleware=middleware)

        return wrapper

    @classmethod
    def post(cls: type[route], path: str, *, middleware: Sequence[Middleware | ASGIMiddleware] | None = None) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["POST"], middleware=middleware)

        return wrapper

    @classmethod
    def put(cls: type[route], path: str, *, middleware: Sequence[Middleware | ASGIMiddleware] | None = None) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["PUT"], middleware=middleware)

        return wrapper

    @classmethod
    def delete(cls: type[route], path: str, *, middleware: Sequence[Middleware | ASGIMiddleware] | None = None) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["DELETE"], middleware=middleware)

        return wrapper

    @classmethod
    def patch(cls: type[route], path: str, *, middleware: Sequence[Middleware | ASGIMiddleware] | None = None) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["PATCH"], middleware=middleware)

        return wrapper

    @classmethod
    def websocket(cls) -> ...: ...

    @classmethod
    def mount(cls) -> ...: ...
