import json
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from rpg_subreddit_processor.entities import ROOT_NODE_PARENT_ID, RedditNode
from rpg_subreddit_processor.utils import KeyValueStoreTransaction
from rpg_subreddit_processor.utils.common_paths import ProcessingStage, processing_stage_directory

from .arctic_shift_comment import ArcticShiftComment
from .arctic_shift_post import ArcticShiftPost


class SubredditFilePair(NamedTuple):
    subreddit: str
    posts_path: Path
    comments_path: Path


def _parse_arctic_shift_posts(file_path: str | Path) -> Iterator[ArcticShiftPost]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                yield ArcticShiftPost(**data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                ) from e
            except Exception as e:
                # Re-raise with line number context for better debugging
                raise ValueError(f"Error parsing line {line_num}: {e}") from e


def _parse_arctic_shift_comments(file_path: str | Path) -> Iterator[ArcticShiftComment]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                yield ArcticShiftComment(**data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                ) from e
            except Exception as e:
                # Preserve the original exception as context while adding line information.
                raise ValueError(f"Error parsing line {line_num}: {e}") from e


def clean_post_text(title: str, body: str) -> str:
    """Normalize and combine title/body text into a single string."""

    title_text = title or ""
    body_text = body or ""
    full_text: str
    if not body_text.startswith(title_text):
        full_text = title_text + "\n" + body_text
    else:
        full_text = body_text

    strings_to_strip = [
        "[BitD]",
        "[BoB]",
        "[S&V]",
        "[Band of Blades]",
        "[FitD]",
        "[BitD-DC]",
        "[Scum & Villainy]",
        "[FitD / BoB]",
        "[DC]",
        "[Fistful of Darkness]",
        "[BITD]",
        "[FITD]",
        "[World of Dungeons]",
        "[WOD]",
        "[WoD]",
        "[Slugblasters]",
        "[Band of blades]",
        "[Deathmatch Island]",
    ]
    for strip_string in strings_to_strip:
        full_text = full_text.replace(strip_string, "")

    lines: list[str] = full_text.splitlines()
    return " ".join([line.strip() for line in lines])


def _get_unique_string_id(text: str | None, txn: KeyValueStoreTransaction, seen_strings: dict[str, int]) -> int:
    text_value = text or ""
    existing_id: int | None = seen_strings.get(text_value)
    if existing_id is not None:
        return existing_id

    new_id: int = txn.add(text_value)
    seen_strings[text_value] = new_id
    return new_id


def node_from_post(
    post: ArcticShiftPost,
    txn: KeyValueStoreTransaction,
    seen_strings: dict[str, int],
    text_clean: Callable[[str, str], str],
) -> RedditNode:
    body: str = text_clean(post.title or "", post.selftext or "")
    body_id: int = txn.add(body)
    author_id: int = _get_unique_string_id(post.author_fullname or post.author, txn, seen_strings)
    post_fullname: str = post.name or f"t3_{post.id}"
    item_id: int = _get_unique_string_id(post_fullname, txn, seen_strings)
    created_at: datetime = datetime.fromtimestamp(post.created_utc, tz=UTC)
    parent_id: int = ROOT_NODE_PARENT_ID
    ups: int = post.ups or 0
    net_ups: int = post.score or 0
    downs: int = ups - net_ups
    return RedditNode(item_id, author_id, body_id, parent_id, created_at, ups, downs)


def node_from_comment(
    comment: ArcticShiftComment,
    txn: KeyValueStoreTransaction,
    seen_strings: dict[str, int],
) -> RedditNode:
    body_id: int = txn.add(comment.body or "")
    author_id: int = _get_unique_string_id(comment.author_fullname or comment.author, txn, seen_strings)
    comment_fullname: str = comment.name or f"t1_{comment.id}"
    item_id: int = _get_unique_string_id(comment_fullname, txn, seen_strings)
    created_at: datetime = datetime.fromtimestamp(comment.created_utc, tz=UTC)
    parent_id: int = _get_unique_string_id(comment.parent_id, txn, seen_strings)
    ups: int = comment.ups or 0
    downs: int = comment.downs or 0
    return RedditNode(item_id, author_id, body_id, parent_id, created_at, ups, downs)


def arctic_shift_path() -> Path:
    return processing_stage_directory(ProcessingStage.ArcticShift)


def _validate_subreddit_file_pairs_internal(
    posts_subreddits: dict[str, Path],
    comments_subreddits: dict[str, Path],
) -> None:
    posts_only = set(posts_subreddits) - set(comments_subreddits)
    comments_only = set(comments_subreddits) - set(posts_subreddits)

    if not posts_only and not comments_only:
        return

    messages: list[str] = []
    for name in sorted(posts_only):
        messages.append(f"Posts file without matching comments: {posts_subreddits[name].name}")
    for name in sorted(comments_only):
        messages.append(f"Comments file without matching posts: {comments_subreddits[name].name}")
    raise ValueError("Mismatched subreddit files:\n" + "\n".join(messages))


def validate_arctic_shift_directory(
    arctic_shift_dir: Path | None = None,
) -> None:
    directory = arctic_shift_dir if arctic_shift_dir is not None else arctic_shift_path()
    posts_subreddits: dict[str, Path] = {}
    for p in directory.glob("r_*_posts.jsonl"):
        name = p.name.removeprefix("r_").removesuffix("_posts.jsonl")
        posts_subreddits[name] = p

    comments_subreddits: dict[str, Path] = {}
    for p in directory.glob("r_*_comments.jsonl"):
        name = p.name.removeprefix("r_").removesuffix("_comments.jsonl")
        comments_subreddits[name] = p

    _validate_subreddit_file_pairs_internal(posts_subreddits, comments_subreddits)


def iter_subreddit_file_pairs(
    arctic_shift_dir: Path | None = None,
) -> Iterator[SubredditFilePair]:
    directory = arctic_shift_dir if arctic_shift_dir is not None else arctic_shift_path()

    posts_subreddits: dict[str, Path] = {}
    for p in directory.glob("r_*_posts.jsonl"):
        name = p.name.removeprefix("r_").removesuffix("_posts.jsonl")
        posts_subreddits[name] = p

    comments_subreddits: dict[str, Path] = {}
    for p in directory.glob("r_*_comments.jsonl"):
        name = p.name.removeprefix("r_").removesuffix("_comments.jsonl")
        comments_subreddits[name] = p

    _validate_subreddit_file_pairs_internal(posts_subreddits, comments_subreddits)

    for name in sorted(posts_subreddits):
        yield SubredditFilePair(name, posts_subreddits[name], comments_subreddits[name])


def posts_file_from_subreddit_name(subreddit: str) -> Path:
    filename = "r_" + subreddit + "_posts.jsonl"
    return arctic_shift_path() / filename


def comments_file_from_subreddit_name(subreddit: str) -> Path:
    filename = "r_" + subreddit + "_comments.jsonl"
    return arctic_shift_path() / filename


def _create_nodes_from_arctic_shift_data(
    posts_path: Path, comments_path: Path, txn: KeyValueStoreTransaction
) -> Iterator[RedditNode]:
    seen_strings: dict[str, int] = {}
    for post in _parse_arctic_shift_posts(posts_path):
        post_node = node_from_post(post, txn, seen_strings, clean_post_text)
        yield post_node

    for comment in _parse_arctic_shift_comments(comments_path):
        comment_node = node_from_comment(comment, txn, seen_strings)
        yield comment_node
