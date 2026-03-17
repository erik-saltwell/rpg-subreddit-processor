from __future__ import annotations

from typing import Protocol

from rpg_subreddit_processor.entities import RedditNode, Subreddit
from rpg_subreddit_processor.utils.key_value_store import KeyValueStoreTransaction


class NodePruningStrategy(Protocol):
    def should_prune(self, node: RedditNode, txn: KeyValueStoreTransaction) -> bool: ...


def prune_nodes(subreddit: Subreddit, strategy: NodePruningStrategy, txn: KeyValueStoreTransaction) -> None:
    nodes_to_prune: list[RedditNode] = []
    for node in subreddit.breadth_first_traversal():
        if strategy.should_prune(node, txn):
            nodes_to_prune.append(node)
    subreddit.prune_nodes(nodes_to_prune)
