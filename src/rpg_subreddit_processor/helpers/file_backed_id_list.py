from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import IO


@dataclass
class FileBackedIDList:
    filepath: Path
    _ids: set[int] = field(default_factory=set, init=False)
    _file: IO[str] = field(init=False, repr=False)

    def _load_from_filepath(self) -> None:
        if self.filepath.exists():
            for line in self.filepath.read_text().splitlines():
                line = line.strip()
                if line:
                    self._ids.add(int(line))

    def __post_init__(self) -> None:
        self._load_from_filepath()
        self._file = self.filepath.open("a")

    def add(self, id: int) -> None:
        self._ids.add(id)
        self._file.write(f"{id}\n")
        self._file.flush()

    def exists(self, id: int) -> bool:
        return id in self._ids

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> FileBackedIDList:
        return self

    def __exit__(
        self, _exc_type: type[BaseException] | None, _exc_val: BaseException | None, _exc_tb: TracebackType | None
    ) -> None:
        self.close()
