import json
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

from rpg_subreddit_processor.entities import ROOT_NODE_PARENT_ID, RedditNode
from rpg_subreddit_processor.utils import KeyValueStoreTransaction

from .arctic_shift_comment import ArcticShiftComment
from .arctic_shift_post import ArcticShiftPost


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
                raise type(e)(f"Error parsing line {line_num}: {e}") from e


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
                # Re-raise with line number context for better debugging
                raise type(e)(f"Error parsing line {line_num}: {e}") from e


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
