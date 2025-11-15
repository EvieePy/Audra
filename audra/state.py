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

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping


class State:
    _state: MutableMapping[str, Any]
    __slots__ = ()

    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        super().__setattr__("_state", state or {})

    def __getattr__(self, name: str) -> Any:
        try:
            self._state[name]
        except KeyError:
            raise AttributeError(f"{self!r} has no attribute {name!r}.")

    def __setattr__(self, name: str, value: Any) -> None:
        self._state[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            self._state.pop(name)
        except KeyError:
            raise AttributeError(f"{self!r} has no attribute {name!r}.")
