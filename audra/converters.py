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
from typing import Any, ClassVar, Protocol, Self


class Converter[T](Protocol):
    pattern: ClassVar[str]
    regex: re.Pattern[str]

    def compile(self, pattern: str, /) -> None: ...

    def convert(self, value: str, /) -> T: ...


class StrConverter(Converter[str]):
    pattern = "[^/]+"

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        inst = super().__new__(cls)

        if inst.pattern:
            inst.compile(inst.pattern)

        return inst

    def compile(self, pattern: str, /) -> None:
        self.regex = re.compile(pattern)

    def convert(self, value: str, /) -> str:
        return str(value)


BASE_CONVERTERS: dict[str, Converter[Any]] = {
    "str": StrConverter(),
}
