from __future__ import annotations

from dataclasses import dataclass, field

import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.entities import RedditNode, Subreddit
from rpg_subreddit_processor.helpers.node_pruner import NodePruningStrategy, prune_root_nodes
from rpg_subreddit_processor.helpers.ollama_helper import OllamaHelper, OllamaModel, labels_match
from rpg_subreddit_processor.protocols import LoggingProtocol
from rpg_subreddit_processor.protocols.logging_protocol import NullLogger
from rpg_subreddit_processor.utils.key_value_store import KeyValueStoreTransaction

from .base_command import BaseCommand


@dataclass
class NonQuestionPruneStrategy(NodePruningStrategy):
    logger: LoggingProtocol
    helper: OllamaHelper = field(default_factory=lambda: OllamaHelper(OllamaModel.RedditRpgQuestionClassifier))

    def should_prune(self, node: RedditNode, txn: KeyValueStoreTransaction) -> bool:
        post_text = node.get_text(txn)
        response: str = self.helper.call_model(post_text)
        prune: bool = labels_match(response, "Other", True, 8, False)
        return prune


class PruneNonQuestions(BaseCommand):
    subreddits: list[str] = []
    logger: LoggingProtocol = NullLogger()  # noqa: B008

    def update_subreddit(self, subreddit: Subreddit, subreddit_name: str, key_store: store.KeyValueStore) -> None:
        strategy: NonQuestionPruneStrategy = NonQuestionPruneStrategy(self.logger)
        with key_store.txn() as txn:
            prune_root_nodes(subreddit, strategy, txn, self.logger)
