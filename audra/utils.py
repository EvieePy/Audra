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
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .types_ import Scope


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
