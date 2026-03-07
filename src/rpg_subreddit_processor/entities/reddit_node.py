"""Reddit node entity."""

from __future__ import annotations

from collections import deque
from collections.abc import Generator, Iterable, MutableSequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import SupportsIndex, cast, overload

from rpg_subreddit_processor.utils.key_value_store import (
    StoreTransaction,
)

ROOT_NODE_PARENT_ID: int = -1


@dataclass(frozen=False, eq=False)
class RedditNode(MutableSequence["RedditNode"]):
    item_id: int
    author_id: int
    text_id: int
    parent_id: int
    created_utc: datetime
    ups: int
    downs: int

    parent: RedditNode | None = field(default=None, repr=False, compare=False, hash=False)
    children: list[RedditNode] = field(
        default_factory=list,
        repr=False,
    )

    @classmethod
    def from_item_id(cls, item_id: int) -> RedditNode:
        """Create a RedditNode with only the item_id set, using defaults for other fields.

        Args:
            item_id: The item identifier for the node.

        Returns:
            A new RedditNode instance with the given item_id and default values.
        """
        return cls(
            item_id=item_id,
            author_id=0,
            text_id=0,
            parent_id=ROOT_NODE_PARENT_ID,
            created_utc=datetime.fromtimestamp(0, tz=UTC),
            ups=0,
            downs=0,
        )

    def get_text(self, txn: StoreTransaction) -> str:
        return txn.get(self.text_id)

    def get_item(self, txn: StoreTransaction) -> str:
        return txn.get(self.item_id)

    def get_author(self, txn: StoreTransaction) -> str:
        return txn.get(self.author_id)

    def is_root(self) -> bool:
        return self.parent_id == ROOT_NODE_PARENT_ID

    def is_leaf(self) -> bool:
        return len(self) == 0

    def breadth_first_traversal(self) -> Generator[RedditNode, None, None]:
        """Iterate over this node and all children nodes in breadth-first order.

        Yields:
            RedditNode instances starting with this node, followed by all
            descendants in breadth-first order.
        """
        queue: deque[RedditNode] = deque([self])

        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def insert(self, index: int, value: RedditNode) -> None:
        """Insert a child node at the given position.

        Args:
            index: Position to insert the child node.
            value: RedditNode to insert.
        """
        value.update_parent(self)
        self.children.insert(index, value)

    def get_root(self) -> RedditNode:
        if self.is_root():
            return self
        potential_root: RedditNode = self
        while not potential_root.is_root():
            assert potential_root.parent is not None
            potential_root = potential_root.parent
        return potential_root

    def count_all_descendants(self) -> int:
        """Count all descendants (children, grandchildren, etc.) of this node.

        Returns:
            Total number of descendant nodes, not including this node.
        """
        return sum(1 for _ in self.breadth_first_traversal()) - 1

    def depth(self) -> int:
        """Compute the depth of this node in the tree.

        Returns:
            The depth, where root nodes have depth 0.
        """
        node: RedditNode = self
        depth = 0
        while not node.is_root():
            depth = depth + 1
            assert node.parent is not None
            node = node.parent
        return depth

    def ancestors(self) -> Generator[RedditNode, None, None]:
        node: RedditNode = self
        while not node.is_root():
            assert node.parent is not None
            node = node.parent
            yield node

    def _clear_parent(self) -> None:
        self.parent = None
        self.parent_id = ROOT_NODE_PARENT_ID

    def update_parent(self, parent: RedditNode) -> None:
        self.parent = parent
        self.parent_id = parent.item_id

    @overload
    def __getitem__(self, index: SupportsIndex) -> RedditNode: ...

    @overload
    def __getitem__(self, index: slice) -> list[RedditNode]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> RedditNode | list[RedditNode]:
        return self.children[index]

    @overload
    def __setitem__(self, index: SupportsIndex, value: RedditNode) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[RedditNode]) -> None: ...

    def __setitem__(
        self,
        index: SupportsIndex | slice,
        value: RedditNode | Iterable[RedditNode],
    ) -> None:
        if isinstance(index, slice):
            for child in self.children[index]:
                child._clear_parent()
            new_children = list(cast(Iterable[RedditNode], value))  # type: ignore
            for child in new_children:
                child.update_parent(self)
            self.children[index] = new_children
        else:
            self.children[index]._clear_parent()
            new_child = cast(RedditNode, value)
            new_child.update_parent(self)
            self.children[index] = new_child

    def __delitem__(self, index: int | slice) -> None:
        """Delete child node(s) at the given index.

        Args:
            index: Integer index or slice for deleting children.
        """
        targets = self.children[index]
        if isinstance(targets, RedditNode):
            targets._clear_parent()
        else:
            for child in targets:
                child._clear_parent()

        del self.children[index]

    def __len__(self) -> int:
        """Return the number of children.

        Returns:
            Count of direct children nodes.
        """
        return len(self.children)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, RedditNode):
            return NotImplemented
        return self.item_id < other.item_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RedditNode):
            return NotImplemented
        return self.item_id == other.item_id

    def __hash__(self) -> int:
        """Return a hash based on the node's item identifier."""
        return hash(self.item_id)

    def __repr__(self) -> str:
        """Return a compact string representation of the node.

        Returns:
            A string showing the node's item_id, parent_id, and number of children.
        """
        parent_id_str = self.parent_id if self.parent_id != ROOT_NODE_PARENT_ID else "ROOT"
        return f"RedditNode(id={self.item_id}, parent={parent_id_str}, children={len(self.children)})"
