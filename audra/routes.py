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

import asyncio
import dataclasses
import inspect
import re
import sys
from typing import TYPE_CHECKING, Any, Self

from .converters import BASE_CONVERTERS, Converter, StrConverter
from .exceptions import (
    HTTPInternalServerError,
    HTTPMethodNotAllowed,
    HTTPNotFound,
    HTTPNotImplemented,
    MiddlewareLoadException,
    RouteAlreadyExists,
)
from .headers import FrozenHeaders
from .middleware.base import ASGIMiddleware, Middleware
from .requests import Request
from .responses import *
from .types_ import Callable, ChildScopeT, HTTPMethod, Receive, RouteCallbackT, Scope, Send
from .utils import *


PY_314 = sys.version_info >= (3, 14)
try:
    from string.templatelib import Template  # type: ignore

    _has_template = True
except ImportError:
    _has_template = False


if TYPE_CHECKING:
    from collections.abc import Awaitable, Sequence


__all__ = ("Path", "Route", "Router", "route")


type DecoRoute = Callable[[RouteCallbackT | Route], Route]


_pre = r"(?P<parameter>\{\s*(?P<name>[a-zA-Z_][A-Za-z0-9_\-]*)\s*(\:?\s*(?P<annotation>[a-zA-Z_][A-Za-z0-9_\-]*)?\s*)\})\/?"
PARAM_RE: re.Pattern[str] = re.compile(_pre)


@dataclasses.dataclass()
class Path:
    path: str
    regex: re.Pattern[str]
    converters: dict[str, Converter[Any]]


class Route(Middleware):
    __route_name__: str

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        inst = super().__new__(cls)
        name = kwargs.get("name") or args[0].__name__
        inst.__route_name__ = name

        return inst

    def __init__(
        self,
        coro: RouteCallbackT,
        *,
        path: str,
        methods: list[HTTPMethod],
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
        name: str | None = None,
    ) -> None:
        methods = [m.upper() for m in methods]  # type: ignore [Reason: Type-Checker doesn't understand safety]
        if "GET" in methods:
            methods.append("HEAD")

        self._methods: set[HTTPMethod] = set(methods)
        self._middleware: list[Middleware | ASGIMiddleware] = list(middleware) if middleware else []
        self._raw_path = path
        self._coro = coro

        converters_ = BASE_CONVERTERS | (converters or {})
        self._converters: dict[str, Converter[Any]] = converters_

        self._path = self.compile_path(self._raw_path)
        self._has_router: bool = False

    def update_converters(self, converters: dict[str, Converter[Any]]) -> None:
        converters.update(self._converters)
        self._converters.update(converters)

        # Ensure converters are updated into our Path...
        self.compile_path(self.raw_path)

    def _unwrap_coro(self, coro: Any, *, request: Request) -> Awaitable[Any]:
        func = unwrap_function(coro)

        if asyncio.iscoroutinefunction(func) or (callable(func) and asyncio.iscoroutinefunction(func.__call__)):
            return func(request)

        if not inspect.isawaitable(func):
            raise TypeError("Route callback must be an awaitable or coroutine function.")

        return func

    def _check_falsey(self, resp: Any) -> bool:
        return resp in FALSEY_RESP and not resp

    def _check_template(self, returned: Any) -> bool:
        if not PY_314:
            return False

        if not _has_template:
            return False

        return isinstance(returned, Template)  # type: ignore

    def _sanitize_template(self, t: Any) -> ...:
        if not PY_314:
            raise RuntimeError("Cannot sanitize template strings. Python >= 3.14 required.")

        if not _has_template:
            raise RuntimeError("Cannot sanitize template strings. Python >= 3.14 required.")

    @property
    def path(self) -> Path:
        return self._path

    @property
    def raw_path(self) -> str:
        return self._raw_path

    def compile_path(self, path: str, /) -> Path:
        index: int = 0
        regex: str = "^"
        converters: dict[str, Converter[Any]] = {}

        for match in PARAM_RE.finditer(path):
            escaped = re.escape(path[index : match.start()])

            name = match.group("name")
            annotation = match.group("annotation")

            if not annotation:
                annotation = "str"

            converter: Converter[Any] = self._converters.get(annotation, StrConverter())
            converters[name] = converter

            regex += f"{escaped.removesuffix('/')}/"
            regex += f"(?P<{name}>{converter.pattern})"

            index = match.end()

        regex += f"{path[index:]}$"
        compiled = re.compile(regex)

        return Path(path=path, regex=compiled, converters=converters)

    async def match(self, path: str, method: HTTPMethod) -> tuple[bool | None, ChildScopeT]:
        params: dict[str, Any] = {}
        child_scope: ChildScopeT = {"params": params}
        # True: Full Match
        # False: No Match
        # None: Partial Match (E.g. Path matches but method isn't allowed)

        # First case can shortcut and doesn't need to do any parameter matching...
        if path == self._raw_path:
            return (True, child_scope) if method in self._methods else (None, child_scope)

        # Try and match the path against the compiled path...
        match = self._path.regex.match(path)

        # Second case: there is no match...
        if not match:
            return False, child_scope

        # Third case: There is a match on the path but method is not available...
        if method not in self._methods:
            return None, child_scope

        # Convert path parameters...
        for name, value in match.groupdict().items():
            converter = self._path.converters.get(name, StrConverter())

            if asyncio.iscoroutinefunction(converter.convert):
                param = await converter.convert(value)
            else:
                param = converter.convert(value)

            params[name] = param

        child_scope["params"] = params
        return True, child_scope

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
            headers = FrozenHeaders({"Allow": ", ".join(self._methods)})
            raise HTTPMethodNotAllowed(headers=headers)

        await self.app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: ...

        assert scope["type"] == "http"
        resp: BaseResponse

        request = Request(scope, receive, send)
        returned: Any = await self._unwrap_coro(self._coro, request=request)

        # Check Falsey strings, bytes; Other falsey types may be more appropriate as their type...
        # E.g. {} would be empty JSON...
        if self._check_falsey(returned):
            resp = EmptyResponse()
        elif isinstance(returned, BaseResponse):
            resp = returned
        elif isinstance(returned, (dict, list, tuple)):
            # TODO: JSONResponse
            resp = EmptyResponse()
        elif isinstance(returned, (str, bytes)):
            resp = PlainTextResponse(returned)
        elif self._check_template(returned):
            resp = HTMLResponse(self._sanitize_template(returned))
        else:
            raise HTTPInternalServerError

        await resp(scope, receive, send)


class Router(Middleware):
    def __init__(
        self,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> None:
        self._routes: list[Route] = []
        self._converters = converters or BASE_CONVERTERS.copy()

    def add_route(self, route: Route) -> None:
        # TODO: Check for duplicates...
        if route._has_router:
            raise RouteAlreadyExists(f"The Route {route!r} has already been added.")

        route.update_converters(self._converters)
        self._routes.append(route)

        route._has_router = True

    async def resolve_path(self, scope: Scope) -> tuple[Route | None, ChildScopeT]:
        assert scope["type"] == "http"

        partial: Route | None = None
        path: str = get_route_path(scope)
        method: HTTPMethod = scope["method"]

        for route in self._routes:
            matched, child_scope = await route.match(path, method)

            if matched:
                return route, child_scope

            elif matched is None:
                partial = route

        if partial is not None:
            headers = FrozenHeaders({"Allow": ", ".join(partial._methods)})
            raise HTTPMethodNotAllowed(headers=headers)

        return None, {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return

        route, child_scope = await self.resolve_path(scope)
        if not route:
            raise HTTPNotFound

        original = scope.get("params", {})
        original.update(child_scope.get("params", {}))

        scope["params"] = original
        await route.invoke(scope, receive, send)


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
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=methods, middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def _wrapper(
        cls: type[route],
        func: RouteCallbackT | Route,
        *,
        path: str,
        methods: list[HTTPMethod],
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> Route:
        if isinstance(func, Route):
            raise RouteAlreadyExists(
                f"{func.__route_name__!r} is already a Route. "
                f"Consider using the '@route(path='{path}', methods=[...])' decorator to pass multiple methods instead."
            )

        return Route(func, path=path, methods=methods, middleware=middleware, converters=converters)

    @classmethod
    def get(
        cls: type[route],
        path: str,
        *,
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["GET"], middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def post(
        cls: type[route],
        path: str,
        *,
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["POST"], middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def put(
        cls: type[route],
        path: str,
        *,
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["PUT"], middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def delete(
        cls: type[route],
        path: str,
        *,
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["DELETE"], middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def patch(
        cls: type[route],
        path: str,
        *,
        middleware: Sequence[Middleware | ASGIMiddleware] | None = None,
        converters: dict[str, Converter[Any]] | None = None,
    ) -> DecoRoute:
        def wrapper(func: RouteCallbackT | Route) -> Route:
            return cls._wrapper(func, path=path, methods=["PATCH"], middleware=middleware, converters=converters)

        return wrapper

    @classmethod
    def websocket(cls) -> ...: ...

    @classmethod
    def mount(cls) -> ...: ...
