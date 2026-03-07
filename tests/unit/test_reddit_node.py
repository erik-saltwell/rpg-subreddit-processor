from __future__ import annotations

from datetime import datetime

import pytest

from rpg_subreddit_processor.entities import ROOT_NODE_PARENT_ID, RedditNode
from rpg_subreddit_processor.utils import StoreTransaction

from .reddit_node_test_helper import (
    create_simple_node,
    node_one,
    node_one_a,
    node_two,
    node_unique,
    validate_node_equality,
)


class IdentityStoreTransaction(StoreTransaction):
    def add(self, text: str) -> int:
        return int(text)

    def get(self, key: int) -> str:
        return str(key)


class DictStoreTransaction(StoreTransaction):
    def __init__(self, values: dict[int, str]) -> None:
        self._values = values

    def add(self, text: str) -> int:
        raise NotImplementedError

    def get(self, key: int) -> str:
        return self._values[key]


@pytest.fixture()
def sample_tree() -> list[RedditNode]:
    # 0
    # ├── 1
    # │   ├── 2
    # │   └── 3
    # │       └── 4
    # ├── 5
    # └── 6
    #     └── 7
    #         └── 8
    #             └── 9
    nodes = [create_simple_node(n) for n in range(0, 10)]
    nodes[0].parent_id = ROOT_NODE_PARENT_ID
    nodes[0].append(nodes[1])
    nodes[1].append(nodes[2])
    nodes[1].append(nodes[3])
    nodes[3].append(nodes[4])
    nodes[0].append(nodes[5])
    nodes[0].append(nodes[6])
    nodes[6].append(nodes[7])
    nodes[7].append(nodes[8])
    nodes[8].append(nodes[9])

    return nodes


def test_simple_value_access():
    validate_node_equality(
        node=node_unique(),
        item_id=61,
        author_id=62,
        text_id=63,
        parent_id=64,
        created_utc=datetime.fromtimestamp(65),
        ups=66,
        downs=67,
    )
    validate_node_equality(
        node=node_one(),
        item_id=1,
        author_id=1,
        text_id=1,
        parent_id=1,
        created_utc=datetime.fromtimestamp(1),
        ups=1,
        downs=1,
    )


def test_equality() -> None:
    assert node_one() == node_one_a()
    assert node_one() == node_one()
    assert node_one() != node_two()
    assert node_two() != node_one_a()
    node: RedditNode = node_one()
    assert node == node


def test_get_text_values() -> None:
    txn: IdentityStoreTransaction = IdentityStoreTransaction()
    assert node_unique().get_item(txn) == "61"
    assert node_unique().get_author(txn) == "62"
    assert node_unique().get_text(txn) == "63"


def test_hash_uses_only_item_id() -> None:
    """Hash nodes using only the item_id field."""

    assert hash(node_one()) == hash(1)
    assert hash(node_one()) != hash(node_two())
    assert hash(node_one()) == hash(node_one_a())


def test_bfs(sample_tree: list[RedditNode]) -> None:
    assert [1, 2, 3] == [1, 2, 3]
    assert [1, 2, 4] != [1, 2, 3]
    assert [
        1,
        2,
    ] != [1, 2, 3]
    output: list[int] = []
    for node in sample_tree[0].breadth_first_traversal():
        output.append(node.item_id)
    assert output == [0, 1, 5, 6, 2, 3, 7, 4, 8, 9]


def test_tree_data(sample_tree: list[RedditNode]) -> None:
    root: RedditNode = sample_tree[0]
    assert root.is_root()
    assert root.depth() == 0
    assert not root.is_leaf()
    leaf: RedditNode = sample_tree[9]
    assert not leaf.is_root()
    assert leaf.is_leaf()
    assert leaf.depth() == 4


class TestParentManagement:
    """Tests that parent/parent_id are correctly maintained on add, remove, and set."""

    def test_append_sets_parent(self, sample_tree: list[RedditNode]) -> None:
        new_node = create_simple_node(99)
        old_children_len = len(sample_tree[5])
        sample_tree[5].append(new_node)
        assert new_node.parent is sample_tree[5]
        assert new_node.parent_id == sample_tree[5].item_id
        assert new_node in sample_tree[5].children
        assert len(sample_tree[5]) == old_children_len + 1

    def test_insert_sets_parent(self, sample_tree: list[RedditNode]) -> None:
        new_node = create_simple_node(99)
        old_len = len(sample_tree[0])
        sample_tree[0].insert(0, new_node)
        assert new_node.parent is sample_tree[0]
        assert new_node.parent_id == sample_tree[0].item_id
        assert sample_tree[0].children[0] is new_node
        assert len(sample_tree[0]) == old_len + 1

    def test_append_sets_parent_on_fixture_nodes(self, sample_tree: list[RedditNode]) -> None:
        for node in sample_tree[1:]:
            assert node.parent is not None, f"node {node.item_id} has no parent"
            assert node.parent_id == node.parent.item_id, (
                f"node {node.item_id}: parent_id={node.parent_id} != parent.item_id={node.parent.item_id}"
            )

    def test_delitem_clears_parent(self, sample_tree: list[RedditNode]) -> None:
        child = sample_tree[5]  # direct child of root
        old_len = len(sample_tree[0])
        del sample_tree[0][1]  # nodes[5] is at index 1 of root's children
        assert child.parent is None
        assert child.parent_id == ROOT_NODE_PARENT_ID
        assert child not in sample_tree[0].children
        assert len(sample_tree[0]) == old_len - 1

    def test_remove_clears_parent(self, sample_tree: list[RedditNode]) -> None:
        child = sample_tree[2]  # child of node 1
        old_len = len(sample_tree[1])
        sample_tree[1].remove(child)
        assert child.parent is None
        assert child.parent_id == ROOT_NODE_PARENT_ID
        assert child not in sample_tree[1].children
        assert len(sample_tree[1]) == old_len - 1

    def test_pop_clears_parent(self, sample_tree: list[RedditNode]) -> None:
        old_len = len(sample_tree[1])
        child = sample_tree[1].pop(0)  # pops node 2
        assert child is sample_tree[2]
        assert child.parent is None
        assert child.parent_id == ROOT_NODE_PARENT_ID
        assert len(sample_tree[1]) == old_len - 1

    def test_setitem_updates_parent(self, sample_tree: list[RedditNode]) -> None:
        old_child = sample_tree[1]  # node 1, child of root at index 0
        old_len = len(sample_tree[0])
        new_node = create_simple_node(99)
        sample_tree[0][0] = new_node
        # old child cleared
        assert old_child.parent is None
        assert old_child.parent_id == ROOT_NODE_PARENT_ID
        # new child set
        assert new_node.parent is sample_tree[0]
        assert new_node.parent_id == sample_tree[0].item_id
        # length unchanged (replacement)
        assert len(sample_tree[0]) == old_len

    def test_setitem_slice_updates_parents(self, sample_tree: list[RedditNode]) -> None:
        old_children = list(sample_tree[0].children)  # [1, 5, 6]
        old_len = len(sample_tree[0])
        new_a = create_simple_node(97)
        new_b = create_simple_node(98)
        sample_tree[0][0:2] = [new_a, new_b]
        # old children cleared
        for old in old_children[:2]:
            assert old.parent is None
            assert old.parent_id == ROOT_NODE_PARENT_ID
        # new children set
        for new in [new_a, new_b]:
            assert new.parent is sample_tree[0]
            assert new.parent_id == sample_tree[0].item_id
        # replaced 2 with 2, length unchanged
        assert len(sample_tree[0]) == old_len

    def test_delitem_slice_clears_parents(self, sample_tree: list[RedditNode]) -> None:
        children_to_remove = list(sample_tree[0].children[:2])  # [1, 5]
        del sample_tree[0][0:2]
        for child in children_to_remove:
            assert child.parent is None
            assert child.parent_id == ROOT_NODE_PARENT_ID
        assert len(sample_tree[0].children) == 1  # only node 6 remains
