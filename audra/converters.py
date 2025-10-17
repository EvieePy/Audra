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

import re
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, Protocol, Self


class _BaseConverter[T](Protocol):
    pattern: ClassVar[str]
    regex: re.Pattern[str]
    convert: Callable[..., Awaitable[T] | T]

    def compile(self, pattern: str, /) -> None: ...


class Converter[T](_BaseConverter[T]):

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        inst = super().__new__(cls)

        if inst.pattern:
            inst.compile(inst.pattern)

        return inst

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(regex={self.regex.pattern!r})"
    
    def compile(self, pattern: str, /) -> None:
        raise NotImplementedError("Implementations of Converter must implement this method.")


class StrConverter(Converter[str]):
    pattern = "[^/]+"

    def compile(self, pattern: str, /) -> None:
        self.regex = re.compile(pattern)

    def convert(self, value: str, /) -> str:
        return str(value)
    

class IntConverter(Converter[int]):
    pattern = r"[\d]+"
    
    def compile(self, pattern: str) -> None:
        self.regex = re.compile(pattern)
        
    def convert(self, value: str, /) -> int:
        return int(value)


BASE_CONVERTERS: dict[str, Converter[Any]] = {
    "str": StrConverter(),
    "int": IntConverter(),
}
