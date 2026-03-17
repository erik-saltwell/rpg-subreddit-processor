from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

_DATA_DIR: Path = Path("data")
_FRAGMENTS_DIR: Path = Path("fragments")
_ARCTIC_SHIFT_DIR: Path = Path("arctic_shift")
_INITIAL_SUBREDDIT_TREES_DIR: Path = Path("initial_subreddit_trees")
_KEYSTORES_DIR: Path = Path("key_stores")
_POSTS_FILENAME: Path = Path("posts.msgpack")


def ensure_directory(dir: Path) -> None:
    dir.mkdir(parents=True, exist_ok=True)


def data_path() -> Path:
    """Return the path to the computed datasets directory under outputs."""
    return _DATA_DIR


def fragments_path() -> Path:
    """Return the shared fragments directory path."""
    return _FRAGMENTS_DIR


def _key_stores_path() -> Path:
    return data_path() / _KEYSTORES_DIR


def arctic_shift_path() -> Path:
    return data_path() / _ARCTIC_SHIFT_DIR


def _initial_subreddit_trees_path() -> Path:
    return data_path() / _INITIAL_SUBREDDIT_TREES_DIR


def key_store_path(subreddit: str) -> Path:
    return_value: Path = _key_stores_path() / subreddit / Path("lmdb")
    ensure_directory(return_value)
    return return_value


def initial_subreddit_path(subreddit: str) -> Path:
    return_value: Path = _initial_subreddit_trees_path() / subreddit
    ensure_directory(return_value)
    return return_value


def posts_file(subreddit: str, base_directory: Path) -> Path:
    return base_directory / Path(subreddit) / _POSTS_FILENAME


def iterate_subreddits(base_directory: Path) -> Iterator[Path]:
    for child in base_directory.iterdir():
        if child.is_dir():
            yield child / Path("posts") / _POSTS_FILENAME
