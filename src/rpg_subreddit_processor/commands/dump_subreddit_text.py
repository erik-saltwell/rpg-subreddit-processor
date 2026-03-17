from __future__ import annotations

import rpg_subreddit_processor.utils.common_paths as common_paths
import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.entities import Subreddit
from rpg_subreddit_processor.protocols import CommmandProtocol, LoggingProtocol
from rpg_subreddit_processor.protocols.logging_protocol import NullLogger


class DumpSubredditText(CommmandProtocol):
    subreddits: list[str] = []
    logger: LoggingProtocol = NullLogger()  # noqa: B008

    def execute(self, logger: LoggingProtocol) -> None:
        self.logger = logger
        for subreddit in self.subreddits:
            self.process_subreddit(subreddit)

    def process_subreddit(self, subreddit_name: str) -> None:
        msgpack_path = common_paths.posts_file(
            subreddit_name, common_paths.processing_stage_directory(common_paths.ProcessingStage.Converted)
        )
        subreddit = Subreddit.from_msgpack_file(msgpack_path, self.logger)
        with store.KeyValueStoreManager(common_paths.key_store_path(subreddit_name)) as store_mgr:
            key_store = store_mgr.store(subreddit_name)
            for node in subreddit.breadth_first_traversal():
                print(key_store.get(node.text_id))
