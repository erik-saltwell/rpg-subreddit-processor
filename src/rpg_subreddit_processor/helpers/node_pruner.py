from __future__ import annotations

from pathlib import Path
from typing import Protocol

from rpg_subreddit_processor.entities import RedditNode, Subreddit
from rpg_subreddit_processor.protocols import LoggingProtocol
from rpg_subreddit_processor.utils.key_value_store import KeyValueStoreTransaction

from .file_backed_id_list import FileBackedIDList


class NodePruningStrategy(Protocol):
    def should_prune(self, node: RedditNode, txn: KeyValueStoreTransaction) -> bool: ...


def prune_all_nodes(
    subreddit: Subreddit,
    strategy: NodePruningStrategy,
    txn: KeyValueStoreTransaction,
    pruned_items_filepath: Path,
    kept_items_filepath: Path,
    logger: LoggingProtocol,
) -> None:
    with FileBackedIDList(kept_items_filepath) as kept_list, FileBackedIDList(pruned_items_filepath) as pruned_list:
        nodes_to_prune: list[RedditNode] = []
        total = subreddit.count_all_nodes()
        with logger.progress("Evaluating nodes...", total) as progress:
            for node in subreddit.breadth_first_traversal():  # traverse all nodes, not just root nodes
                if pruned_list.exists(node.item_id):
                    nodes_to_prune.append(node)
                elif not kept_list.exists(node.item_id):
                    if strategy.should_prune(node, txn):
                        nodes_to_prune.append(node)
                        pruned_list.add(node.item_id)
                    else:
                        kept_list.add(node.item_id)
                progress.advance()
        subreddit.prune_nodes(nodes_to_prune)
        kept = subreddit.count_all_nodes()
        logger.report_message(f"  Pruned {len(nodes_to_prune)} nodes, kept {kept} nodes.")


def prune_root_nodes(
    subreddit: Subreddit,
    strategy: NodePruningStrategy,
    txn: KeyValueStoreTransaction,
    pruned_items_filepath: Path,
    kept_items_filepath: Path,
    logger: LoggingProtocol,
) -> None:
    with FileBackedIDList(kept_items_filepath) as kept_list, FileBackedIDList(pruned_items_filepath) as pruned_list:
        nodes_to_prune: list[RedditNode] = []
        total = subreddit.count_posts()
        with logger.progress("Evaluating nodes...", total) as progress:
            for node in subreddit:  # traverse only root nodes
                if pruned_list.exists(node.item_id):
                    nodes_to_prune.append(node)
                elif not kept_list.exists(node.item_id):
                    if strategy.should_prune(node, txn):
                        nodes_to_prune.append(node)
                        pruned_list.add(node.item_id)
                    else:
                        kept_list.add(node.item_id)
                progress.advance()
        subreddit.prune_nodes(nodes_to_prune)
        kept = subreddit.count_posts()
        logger.report_message(f"  Initial Count: {total}. Pruned {len(nodes_to_prune)} nodes, kept {kept} nodes.")
