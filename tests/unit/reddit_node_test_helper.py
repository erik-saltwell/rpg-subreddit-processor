from datetime import datetime

from rpg_subreddit_processor.entities.reddit_node import RedditNode


def validate_node_equality(
    node: RedditNode,
    item_id: int,
    author_id: int,
    text_id: int,
    parent_id: int,
    created_utc: datetime,
    ups: int,
    downs: int,
) -> None:
    assert node.item_id == item_id
    assert node.author_id == author_id
    assert node.text_id == text_id
    assert node.parent_id == parent_id
    assert node.created_utc == created_utc
    assert node.ups == ups
    assert node.downs == downs


def validate_simple_node(node: RedditNode, value: int) -> None:
    """Validate that a node created by create_simple_node(value) has the expected attributes.

    Does not check parent_id because tree operations update it.
    """
    assert node.item_id == value
    assert node.author_id == value
    assert node.text_id == value
    assert node.created_utc == datetime.fromtimestamp(float(value))
    assert node.ups == value
    assert node.downs == value


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
