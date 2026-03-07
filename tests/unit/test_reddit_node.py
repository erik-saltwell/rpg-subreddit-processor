from __future__ import annotations

from datetime import datetime

from rpg_subreddit_processor.entities import RedditNode

from .reddit_node_test_helper import validate_node_equality


def create_simple_node(value: int) -> RedditNode:
    float_value: float = float(value)
    return RedditNode(
        item_id=value,
        author_id=value,
        text_id=value,
        parent_id=value,
        created_utc=datetime.fromtimestamp(float_value),
        ups=value,
        downs=value,
    )


def node_one() -> RedditNode:
    return create_simple_node(1)


def node_two() -> RedditNode:
    return create_simple_node(2)


def node_one_a() -> RedditNode:
    return RedditNode(
        item_id=1,
        author_id=2,
        text_id=2,
        parent_id=2,
        created_utc=datetime.fromtimestamp(2),
        ups=2,
        downs=2,
    )


def node_unique() -> RedditNode:
    return RedditNode(
        item_id=61,
        author_id=62,
        text_id=63,
        parent_id=64,
        created_utc=datetime.fromtimestamp(65),
        ups=66,
        downs=67,
    )


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
