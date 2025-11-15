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

Copyright © 2018, [Encode OSS Ltd](https://www.encode.io/)
Copyright © 2025, Marcelo Trylesinski
See: https://github.com/Kludex/starlette/blob/main/LICENSE.md for license details.

Copyright (c) 2017 - Present PythonistaGuild (https://github.com/PythonistaGuild/TwitchIO/blob/main/twitchio/utils.py)
Copyright (c) 2015-present Rapptz (https://github.com/Rapptz/discord.py/blob/master/discord/utils.py)
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from .types_ import Scope


__all__ = ("FALSEY_RESP", "MISSING", "get_route_path", "unwrap_function")


def get_route_path(scope: Scope) -> str:
    assert scope["type"] != "lifespan"

    path: str = scope["path"]
    root_path = scope.get("root_path", "")

    if not root_path:
        return path

    if not path.startswith(root_path):
        return path

    if path == root_path:
        return ""

    if path[len(root_path)] == "/":
        return path[len(root_path) :]

    return path


def unwrap_function(function: Callable[..., Any], /) -> Callable[..., Any]:
    partial = functools.partial

    while True:
        if hasattr(function, "__wrapped__"):
            function = function.__wrapped__  # type: ignore
        elif isinstance(function, partial):
            function = function.func
        else:
            return function


FALSEY_RESP = [str, bytes, bytearray, memoryview, None]


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()
