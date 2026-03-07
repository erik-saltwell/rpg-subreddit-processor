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
    assert parent_id == parent_id
    assert node.created_utc == created_utc
    assert node.ups == ups
    assert node.downs == downs
