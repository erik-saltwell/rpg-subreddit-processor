from __future__ import annotations

import pytest

from rpg_subreddit_processor.entities import ROOT_NODE_PARENT_ID, Subreddit
from rpg_subreddit_processor.entities.reddit_node import RedditNode

from .reddit_node_test_helper import create_simple_node, validate_simple_node

SAMPLE_SUBREDDIT_NAME: str = "sample"


@pytest.fixture()
def sample_subreddit() -> Subreddit:
    # _root (synthetic)
    # ├── 0 (post)
    # │   ├── 3
    # │   │   └── 5
    # │   └── 4
    # ├── 1 (post)
    # │   └── 6
    # │       └── 7
    # └── 2 (post)
    #     ├── 8
    #     └── 9
    nodes = [create_simple_node(n) for n in range(10)]

    # Mark posts as root nodes
    for i in [0, 1, 2]:
        nodes[i].parent_id = ROOT_NODE_PARENT_ID

    subreddit: Subreddit = Subreddit(SAMPLE_SUBREDDIT_NAME)

    # Add posts to subreddit
    subreddit.append(nodes[0])
    subreddit.append(nodes[1])
    subreddit.append(nodes[2])

    # Post 0's comments
    nodes[0].append(nodes[3])
    nodes[0].append(nodes[4])
    nodes[3].append(nodes[5])

    # Post 1's comments
    nodes[1].append(nodes[6])
    nodes[6].append(nodes[7])

    # Post 2's comments
    nodes[2].append(nodes[8])
    nodes[2].append(nodes[9])

    return subreddit


def test_sample_subreddit_structure(sample_subreddit: Subreddit) -> None:
    """Walk the sample subreddit and verify structure and node attributes."""
    # Validate all 10 nodes via BFS
    bfs_ids: list[int] = []
    for node in sample_subreddit.breadth_first_traversal():
        validate_simple_node(node, node.item_id)
        bfs_ids.append(node.item_id)

    # BFS order: posts first (0,1,2), then their children level by level
    assert bfs_ids == [0, 1, 2, 3, 4, 6, 8, 9, 5, 7]

    # Verify parent relationships for posts (direct children of synthetic root)
    for i in range(3):
        post: RedditNode = sample_subreddit[i]
        assert post.parent is not None
        assert post.parent.item_id == ROOT_NODE_PARENT_ID

    # Verify parent relationships for comments
    expected_parents: dict[int, int] = {
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 6,
        8: 2,
        9: 2,
    }
    for node in sample_subreddit.breadth_first_traversal():
        if node.item_id in expected_parents:
            assert node.parent is not None
            assert node.parent.item_id == expected_parents[node.item_id]
            assert node.parent_id == expected_parents[node.item_id]

    # Verify children counts
    assert len(sample_subreddit[0]) == 2  # post 0: nodes 3, 4
    assert len(sample_subreddit[1]) == 1  # post 1: node 6
    assert len(sample_subreddit[2]) == 2  # post 2: nodes 8, 9


def test_subreddit_length(sample_subreddit: Subreddit) -> None:
    assert len(sample_subreddit) == 3
    assert sample_subreddit.post_count() == 3
    assert sample_subreddit.comment_count() == 7


class TestSubredditRootMutations:
    """Tests for add/remove/set at the subreddit root level."""

    def test_append_sets_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        new_post = create_simple_node(99)
        new_post.parent_id = ROOT_NODE_PARENT_ID
        sample_subreddit.append(new_post)
        assert len(sample_subreddit) == 4
        assert new_post.parent is not None
        assert new_post.parent.item_id == ROOT_NODE_PARENT_ID
        assert new_post in sample_subreddit._root.children

    def test_insert_sets_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        new_post = create_simple_node(99)
        new_post.parent_id = ROOT_NODE_PARENT_ID
        sample_subreddit.insert(0, new_post)
        assert len(sample_subreddit) == 4
        assert sample_subreddit[0] is new_post
        assert new_post.parent is not None
        assert new_post.parent.item_id == ROOT_NODE_PARENT_ID

    def test_delitem_clears_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        removed_post: RedditNode = sample_subreddit[1]  # post 1
        del sample_subreddit[1]
        assert len(sample_subreddit) == 2
        assert removed_post.parent is None
        assert removed_post.parent_id == ROOT_NODE_PARENT_ID
        assert removed_post not in sample_subreddit._root.children

    def test_remove_clears_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        post_to_remove: RedditNode = sample_subreddit[0]  # post 0
        sample_subreddit.remove(post_to_remove)
        assert len(sample_subreddit) == 2
        assert post_to_remove.parent is None
        assert post_to_remove.parent_id == ROOT_NODE_PARENT_ID

    def test_pop_clears_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        popped: RedditNode = sample_subreddit.pop(0)
        assert popped.item_id == 0
        assert len(sample_subreddit) == 2
        assert popped.parent is None
        assert popped.parent_id == ROOT_NODE_PARENT_ID

    def test_setitem_updates_parent_and_length(self, sample_subreddit: Subreddit) -> None:
        old_post: RedditNode = sample_subreddit[1]
        new_post = create_simple_node(99)
        sample_subreddit[1] = new_post
        # length unchanged
        assert len(sample_subreddit) == 3
        # old post cleared
        assert old_post.parent is None
        assert old_post.parent_id == ROOT_NODE_PARENT_ID
        # new post set
        assert new_post.parent is not None
        assert new_post.parent.item_id == ROOT_NODE_PARENT_ID
        assert sample_subreddit[1] is new_post


def _collect_bfs_fields(subreddit: Subreddit) -> list[tuple[int, int, int, int, int, int, int]]:
    """Return (item_id, author_id, text_id, parent_id, epoch_sec, ups, downs) for each node in BFS order."""
    return [
        (
            n.item_id,
            n.author_id,
            n.text_id,
            n.parent_id,
            int(n.created_utc.timestamp()),
            n.ups,
            n.downs,
        )
        for n in subreddit.breadth_first_traversal()
    ]


def test_msgpack_roundtrip(sample_subreddit: Subreddit) -> None:
    original_fields = _collect_bfs_fields(sample_subreddit)

    data = sample_subreddit.to_msgpack_bytes()
    restored = Subreddit.from_msgpack_bytes(data)

    assert restored.name == sample_subreddit.name
    assert restored.post_count() == sample_subreddit.post_count()
    assert restored.comment_count() == sample_subreddit.comment_count()
    assert _collect_bfs_fields(restored) == original_fields


def test_msgpack_file_roundtrip(tmp_path: pytest.TempdirFactory, sample_subreddit: Subreddit) -> None:
    original_fields = _collect_bfs_fields(sample_subreddit)
    filepath = tmp_path / "test.msgpack"  # type: ignore[operator]

    sample_subreddit.to_msgpack_file(filepath)
    restored = Subreddit.from_msgpack_file(filepath)

    assert restored.name == sample_subreddit.name
    assert restored.post_count() == sample_subreddit.post_count()
    assert restored.comment_count() == sample_subreddit.comment_count()
    assert _collect_bfs_fields(restored) == original_fields
