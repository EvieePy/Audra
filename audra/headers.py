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

from functools import cache
from types import MappingProxyType
from typing import Any, Self


__all__ = ("BytesOrStr", "FrozenHeaders", "Headers")


type BytesOrStr = bytes | str


class Headers(dict[str, BytesOrStr]):
    __slots__ = ()

    def __init__(self, headers: dict[str, BytesOrStr] | Headers | None = None) -> None:
        self.update({k.casefold(): v for k, v in (headers or {}).items()})

    def _handle_duplicates(self, name: str, value: BytesOrStr, /) -> None:
        name = name.replace("_", "-").casefold()

        if name not in self.keys():
            return super().__setitem__(name.casefold(), value)

        old = super().__getitem__(name)
        super().__setitem__(name.casefold(), f"{old}, {value}")

    def append_to_field(self, name: str, value: BytesOrStr, /) -> Self:
        self._handle_duplicates(name, value)
        return self

    def set_field(self, name: str, value: BytesOrStr, /) -> Self:
        super().__setitem__(name, value)
        return self

    def __str__(self) -> str:
        return str(dict(self))

    def __contains__(self, value: object, /) -> bool:
        return super().__contains__(value.casefold()) if isinstance(value, str) else False

    def __missing__(self, _: str, /) -> None:
        return None

    def __delitem__(self, name: str, /) -> None:
        return super().__delitem__(name.casefold())

    def __getitem__(self, name: str, /) -> BytesOrStr:
        return super().__getitem__(name.casefold())

    def __setitem__(self, name: str, value: BytesOrStr, /) -> None:
        name = name.replace("_", "-").casefold()
        super().__setitem__(name, value)

    def __getattr__(self, name: str, /) -> Any:
        name = name.replace("_", "-").casefold()

        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}") from e

    def __setattr__(self, name: str, value: BytesOrStr, /) -> None:
        name = name.replace("_", "-")
        super().__setitem__(name, value)

    def __delattr__(self, name: str, /) -> None:
        name = name.replace("_", "-")
        super().__delitem__(name.casefold())

    def __ior__(self, other: object, /) -> Headers:
        if not isinstance(other, Headers):
            raise TypeError(f"Cannot combine {self.__class__.__name__!r} with {type(other).__name__!r}.")

        return super().__ior__(other)

    def raw(self) -> list[tuple[bytes, bytes]]:
        return [(k.encode("latin-1"), v.encode("latin-1") if isinstance(v, str) else v) for k, v in self.items()]

    def as_dict(self) -> MappingProxyType[str, BytesOrStr]:
        return MappingProxyType(self)


class FrozenHeaders(Headers):
    __slots__ = ()

    def __init__(self, headers: dict[str, BytesOrStr]) -> None:
        super().__init__(headers)

    def __hash__(self) -> int:  # type: ignore
        return hash(repr(sorted(self.items())))

    def __setattr__(self, name: str, value: BytesOrStr, /) -> None:
        raise AttributeError(f"{self.__class__.__name__!r} items cannot be set.")

    def __setitem__(self, name: str, value: BytesOrStr, /) -> None:
        raise AttributeError(f"{self.__class__.__name__!r} items cannot be set.")

    def __ior__(self, other: object, /) -> Headers:
        raise NotImplementedError(f"{self.__class__.__name__!r} cannot be combined.")

    @cache
    def as_tuple(self) -> list[tuple[bytes, bytes]]:  # type: ignore
        return [(k.encode("latin-1"), v.encode("latin-1") if isinstance(v, str) else v) for k, v in self.items()]

    @cache
    def as_dict(self) -> MappingProxyType[str, BytesOrStr]:  # type: ignore
        return MappingProxyType(self)

    def mutable_copy(self) -> Headers:
        return Headers(self)