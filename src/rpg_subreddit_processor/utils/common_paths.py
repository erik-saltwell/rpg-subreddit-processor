from __future__ import annotations

from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path

_DATA_DIR: Path = Path("data")
_FRAGMENTS_DIR: Path = Path("fragments")


class ProcessingStage(StrEnum):
    Converted = "initial_subreddit_trees"
    NonQuestionsPruned = "non_questions_pruned"


def ensure_directory(dir: Path) -> None:
    dir.mkdir(parents=True, exist_ok=True)


def data_path() -> Path:
    """Return the path to the computed datasets directory under outputs."""
    return _DATA_DIR


def fragments_path() -> Path:
    """Return the shared fragments directory path."""
    return _FRAGMENTS_DIR


def subreddit_directory(subreddit: str) -> Path:
    d = data_path() / subreddit
    ensure_directory(d)
    return d


def potential_thanks_file() -> Path:
    return data_path() / "potential_thanks.json"


def arctic_shift_posts_file(subreddit: str) -> Path:
    return subreddit_directory(subreddit) / f"r_{subreddit}_posts.jsonl"


def arctic_shift_comments_file(subreddit: str) -> Path:
    return subreddit_directory(subreddit) / f"r_{subreddit}_comments.jsonl"


def key_store_path(subreddit: str) -> Path:
    return_value: Path = subreddit_directory(subreddit) / "lmdb"
    ensure_directory(return_value)
    return return_value


def posts_file(subreddit: str, stage: ProcessingStage) -> Path:
    return subreddit_directory(subreddit) / f"{stage}.msgpack"


def kept_file(subreddit: str, prefix: str) -> Path:
    return subreddit_directory(subreddit) / f"{prefix}_kept.txt"


def pruned_file(subreddit: str, prefix: str) -> Path:
    return subreddit_directory(subreddit) / f"{prefix}_pruned.txt"


def iterate_subreddit_names() -> Iterator[str]:
    for child in data_path().iterdir():
        if child.is_dir():
            yield child.name
