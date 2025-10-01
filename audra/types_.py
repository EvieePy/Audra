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

from collections.abc import Awaitable, Callable, Coroutine, Iterable
from typing import Any, Concatenate, Literal, NotRequired, ParamSpec, Protocol, TypedDict


__all__ = (
    "HTTPASGI",
    "HTTPScope",
    "LifespanCallbackT",
    "LifespanCallbackT",
    "LifespanMessageT",
    "LifespanScope",
    "LifespanShutdownMessage",
    "LifespanStartupMessage",
)


P = ParamSpec("P")

type PortT = int
type HostT = str

type RawHeadersT = Iterable[tuple[bytes]]  # TODO: Check actual data... vvv
type ClientDataT = tuple[HostT, PortT]
type ServerDataT = tuple[HostT, PortT | None]


type LifespanMessageT = LifespanStartupMessage | LifespanShutdownMessage

type Scope = HTTPScope | WebsocketScope | LifespanScope
type State = dict[str, Any]
type Message = dict[str, Any]

type ReceiveLS = Callable[[], Awaitable[LifespanMessageT]]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]


# TODO: Other types...
# NOTE: Injection type...
type LifespanCallbackT = (
    Callable[Concatenate[Any, State | None, ...], Coroutine[Any, Any, None]]
    | Callable[Concatenate[State | None, ...], Coroutine[Any, Any, None]]
)


class ASGIApp(Protocol):
    app: ASGIApp

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Any: ...


class HTTPASGI(TypedDict):
    version: str
    spec_version: Literal["2.0", "2.1", "2.2", "2.3", "2.4", "2.5"]


class WebsocketASGI(TypedDict):
    version: str
    spec_version: NotRequired[Literal["2.0", "2.1", "2.2", "2.3"]]


class HTTPScope(TypedDict):
    type: Literal["http"]
    asgi: HTTPASGI
    http_version: Literal["1.0", "1.1", "2"]
    method: Literal["GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE", "POST", "PATCH", "CONNECT"]
    scheme: Literal["http", "https"] | str
    path: str
    raw_path: bytes
    query_string: bytes
    root_path: str
    headers: RawHeadersT
    client: ClientDataT | None
    server: ServerDataT | None
    state: NotRequired[State]


class WebsocketScope(TypedDict):
    type: Literal["websocket"]
    asgi: HTTPASGI
    http_version: Literal["1.0", "1.1", "2"]
    scheme: Literal["ws", "wss"] | str
    path: str
    raw_path: bytes
    query_string: bytes
    root_path: str
    headers: RawHeadersT
    client: ClientDataT | None
    server: ServerDataT | None
    subprotocols: Iterable[str]
    state: NotRequired[State]


class LifespanScope(TypedDict):
    type: Literal["lifespan"]
    asgi: HTTPASGI
    state: NotRequired[State]


class LifespanStartupMessage(TypedDict):
    type: Literal["lifespan.startup"]


class LifespanShutdownMessage(TypedDict):
    type: Literal["lifespan.shutdown"]
