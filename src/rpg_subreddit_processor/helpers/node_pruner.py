from __future__ import annotations

from typing import Protocol

from rpg_subreddit_processor.entities import RedditNode, Subreddit
from rpg_subreddit_processor.protocols import LoggingProtocol
from rpg_subreddit_processor.utils.key_value_store import KeyValueStoreTransaction


class NodePruningStrategy(Protocol):
    def should_prune(self, node: RedditNode, txn: KeyValueStoreTransaction) -> bool: ...


def prune_all_nodes(
    subreddit: Subreddit,
    strategy: NodePruningStrategy,
    txn: KeyValueStoreTransaction,
    logger: LoggingProtocol,
) -> None:
    nodes_to_prune: list[RedditNode] = []
    total = subreddit.count_all_nodes()
    with logger.progress("Evaluating nodes...", total) as progress:
        for node in subreddit.breadth_first_traversal():  # traverse all nodes, not just root nodes
            if strategy.should_prune(node, txn):
                nodes_to_prune.append(node)
            progress.advance()
    subreddit.prune_nodes(nodes_to_prune)
    kept = subreddit.count_all_nodes()
    logger.report_message(f"  Pruned {len(nodes_to_prune)} nodes, kept {kept} nodes.")


def prune_root_nodes(
    subreddit: Subreddit,
    strategy: NodePruningStrategy,
    txn: KeyValueStoreTransaction,
    logger: LoggingProtocol,
) -> None:
    nodes_to_prune: list[RedditNode] = []
    total = subreddit.count_posts()
    with logger.progress("Evaluating nodes...", total) as progress:
        for node in subreddit:  # traverse only root nodes
            if strategy.should_prune(node, txn):
                nodes_to_prune.append(node)
            progress.advance()
    subreddit.prune_nodes(nodes_to_prune)
    kept = subreddit.count_posts()
    logger.report_message(f"  Pruned {len(nodes_to_prune)} nodes, kept {kept} nodes.")
