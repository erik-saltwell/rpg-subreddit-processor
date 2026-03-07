from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommonPaths:
    """Resolves and ensures standard project directory paths for a given target mode."""

    DATA_DIR: Path = Path("data")
    FRAGMENTS_DIR: Path = Path("fragments")

    @property
    def data(self) -> Path:
        """Return the path to the computed datasets directory under outputs."""
        return self.DATA_DIR

    @property
    def fragments(self) -> Path:
        """Return the shared fragments directory path."""
        return self.FRAGMENTS_DIR

    @staticmethod
    def get() -> CommonPaths:
        """static constructor to create a CommonPaths object."""
        return CommonPaths()
