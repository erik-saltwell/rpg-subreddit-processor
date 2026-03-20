from __future__ import annotations

import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.entities import Subreddit

from .base_reporting_command import BaseReportingCommand


class DumpSubredditText(BaseReportingCommand):
    def process(self, subreddit: Subreddit, subreddit_name: str, key_store: store.KeyValueStore) -> None:
        for node in subreddit.breadth_first_traversal():
            print(key_store.get(node.text_id))

    def complete(self) -> None:
        pass
