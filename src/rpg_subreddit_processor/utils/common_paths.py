from __future__ import annotations

from pathlib import Path

_DATA_DIR: Path = Path("data")
_FRAGMENTS_DIR: Path = Path("fragments")
_ARCTIC_SHIFT_DIR: Path = Path("arctic_shift")
_INITIAL_SUBREDDIT_TREES_DIR: Path = Path("initial_subreddit_trees")


def data_path() -> Path:
    """Return the path to the computed datasets directory under outputs."""
    return _DATA_DIR


def fragments_path() -> Path:
    """Return the shared fragments directory path."""
    return _FRAGMENTS_DIR


def arctic_shift_path() -> Path:
    return data_path() / _ARCTIC_SHIFT_DIR


def initial_subreddit_trees_path() -> Path:
    return data_path() / _INITIAL_SUBREDDIT_TREES_DIR
