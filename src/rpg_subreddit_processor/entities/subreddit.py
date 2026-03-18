from __future__ import annotations

import json
from collections.abc import Generator, Iterable, Iterator, MutableSequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, SupportsIndex, cast, overload

import msgpack

from rpg_subreddit_processor.protocols import LoggingProtocol
from rpg_subreddit_processor.protocols.logging_protocol import NullLogger, ProgressTask

from .reddit_node import ROOT_NODE_PARENT_ID, RedditNode


@dataclass(frozen=False, eq=True)
class Subreddit(MutableSequence["RedditNode"]):
    name: str
    _root: RedditNode = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Create a *fresh* root per instance, with a fresh timestamp.
        self._root = RedditNode(
            ROOT_NODE_PARENT_ID,
            ROOT_NODE_PARENT_ID,
            ROOT_NODE_PARENT_ID,
            ROOT_NODE_PARENT_ID,
            datetime.now(UTC),
            ROOT_NODE_PARENT_ID,
            ROOT_NODE_PARENT_ID,
        )

    def insert(self, index: int, value: RedditNode) -> None:
        self._root.insert(index, value)

    def to_json_string(self, task: ProgressTask | None = None) -> str:
        def node_to_dict(node: RedditNode) -> dict[str, Any]:
            """Recursively convert a RedditNode and its children to a dict."""
            if task is not None:
                task.advance()
            return {
                "item_id": node.item_id,
                "author_id": node.author_id,
                "text_id": node.text_id,
                "parent_id": node.parent_id,
                "created_utc": node.created_utc.isoformat(),
                "ups": node.ups,
                "downs": node.downs,
                "children": [node_to_dict(child) for child in node.children],
            }

        data = {
            "name": self.name,
            "root": node_to_dict(self._root),
        }
        return json.dumps(data, indent=2)

    def to_json_file(self, filepath: Path, logger: LoggingProtocol = NullLogger()) -> None:  # noqa: B008
        total = self._root.count_all_descendants() + 1
        with logger.progress("Saving", total=total) as task:
            json_string = self.to_json_string(task)
        filepath.write_text(json_string)

    @classmethod
    def from_node_list(
        cls,
        nodes: Iterator[RedditNode],
        subreddit_name: str,
        logger: LoggingProtocol = NullLogger(),  # noqa: B008
    ) -> Subreddit:
        # We know that we will get orphans because of the great reddit data blackout.
        # This drops the orphans intenionally.

        all_nodes: dict[int, RedditNode] = {}
        with logger.progress("Loading nodes") as task:
            for node in nodes:
                all_nodes[node.item_id] = node
                task.advance()

        subreddit: Subreddit = Subreddit(subreddit_name)
        with logger.progress("Building tree", total=len(all_nodes)) as task:
            for node in all_nodes.values():
                if node.is_root():
                    subreddit._root.append(node)
                else:
                    parent: RedditNode | None = all_nodes.get(node.parent_id)
                    if parent is not None:
                        parent.append(node)
                task.advance()
        return subreddit

    @classmethod
    def from_json_string(cls, text: str) -> Subreddit:
        def dict_to_node(node_dict: dict[str, Any]) -> RedditNode:
            """Recursively convert a dict to a RedditNode with children."""
            node = RedditNode(
                item_id=node_dict["item_id"],
                author_id=node_dict["author_id"],
                text_id=node_dict["text_id"],
                parent_id=node_dict["parent_id"],
                created_utc=datetime.fromisoformat(node_dict["created_utc"]),
                ups=node_dict["ups"],
                downs=node_dict["downs"],
            )

            for child_dict in node_dict["children"]:
                child = dict_to_node(child_dict)
                node.append(child)
            return node

        data = json.loads(text)
        subreddit = cls(data["name"])
        subreddit._root = dict_to_node(data["root"])
        return subreddit

    @classmethod
    def from_json_file(cls, filepath: Path) -> Subreddit:
        json_string = filepath.read_text()
        return cls.from_json_string(json_string)

    def to_msgpack_bytes(self, task: ProgressTask | None = None) -> bytes:
        records = []
        for node in self.breadth_first_traversal():
            if task is not None:
                task.advance()
            records.append(
                [
                    node.item_id,
                    node.author_id,
                    node.text_id,
                    node.parent_id,
                    int(node.created_utc.timestamp()),
                    node.ups,
                    node.downs,
                ]
            )
        packed = cast(bytes, msgpack.packb([self.name, records], use_bin_type=True))
        return packed

    def to_msgpack_file(self, filepath: Path, logger: LoggingProtocol = NullLogger()) -> None:  # noqa: B008
        total = self._root.count_all_descendants()
        with logger.progress("Saving (binary)", total=total) as task:
            data = self.to_msgpack_bytes(task)
        filepath.write_bytes(data)

    @classmethod
    def from_msgpack_bytes(cls, data: bytes, logger: LoggingProtocol = NullLogger()) -> Subreddit:  # noqa: B008
        name, records = msgpack.unpackb(data, raw=False)

        def iter_nodes() -> Iterator[RedditNode]:
            for r in records:
                yield RedditNode(
                    item_id=r[0],
                    author_id=r[1],
                    text_id=r[2],
                    parent_id=r[3],
                    created_utc=datetime.fromtimestamp(r[4], tz=UTC),
                    ups=r[5],
                    downs=r[6],
                )

        return cls.from_node_list(iter_nodes(), name, logger)

    @classmethod
    def from_msgpack_file(cls, filepath: Path, logger: LoggingProtocol = NullLogger()) -> Subreddit:  # noqa: B008
        return cls.from_msgpack_bytes(filepath.read_bytes(), logger)

    def breadth_first_traversal(self) -> Generator[RedditNode, None, None]:
        """BFS over the subtree under _root, but skip yielding the root node itself."""
        it: Generator[RedditNode, None, None] = self._root.breadth_first_traversal()

        # Consume the first item (the root) if present
        next(it, None)

        # Yield the remaining nodes
        yield from it

    def sort_recursive(self) -> None:
        self._root.children.sort()
        for node in self.breadth_first_traversal():
            node.children.sort()

    def print_tree(self) -> None:
        for node in self.breadth_first_traversal():
            assert node.parent is not None
            print(f"{node.parent.item_id}->{node.item_id}")

    def count_posts(self) -> int:
        """Return the number of posts (direct children of the root)."""
        return len(self._root)

    def count_comments(self) -> int:
        """Return the number of comments (all descendants minus posts)."""
        return self._root.count_all_descendants() - self.count_posts()

    def count_all_nodes(self) -> int:
        return self._root.count_all_descendants()

    def prune_nodes(self, nodes_to_delete: Iterable[RedditNode]) -> None:
        for node in list(nodes_to_delete):
            if not node.is_root():
                assert node.parent is not None
                node.parent.remove(node)

    @overload
    def __getitem__(self, index: SupportsIndex) -> RedditNode: ...

    @overload
    def __getitem__(self, index: slice) -> list[RedditNode]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> RedditNode | list[RedditNode]:
        # Narrowing makes mypy pick the right overload on RedditNode.__getitem__
        if isinstance(index, slice):
            return self._root[index]
        return self._root[index]

    @overload
    def __setitem__(self, index: SupportsIndex, value: RedditNode) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[RedditNode]) -> None: ...

    def __setitem__(
        self,
        index: SupportsIndex | slice,
        value: RedditNode | Iterable[RedditNode],
    ) -> None:
        # Narrow both unions so mypy can match the correct __setitem__ overload.
        if isinstance(index, slice):
            self._root[index] = value
        else:
            self._root[index] = cast(RedditNode, value)

    def __delitem__(self, index: int | slice) -> None:
        """Delete child node(s) at the given index.

        Args:
            index: Integer index or slice for deleting children.
        """
        del self._root[index]

    def __len__(self) -> int:
        """Return the number of children.

        Returns:
            Count of direct children nodes.
        """
        return len(self._root)
