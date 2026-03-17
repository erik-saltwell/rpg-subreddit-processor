from __future__ import annotations

from abc import ABC
from pathlib import Path

import rpg_subreddit_processor.utils.common_paths as common_paths
import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.entities import Subreddit
from rpg_subreddit_processor.protocols import CommmandProtocol, LoggingProtocol
from rpg_subreddit_processor.protocols.logging_protocol import NullLogger


class BaseCommand(ABC, CommmandProtocol):
    subreddits: list[str] = []

    input_directory: Path
    output_directory: Path
    logger: LoggingProtocol = NullLogger()  # noqa: B008

    def post_message(self, message: str) -> None:
        self.logger.report_message("[blue]" + message + "[/blue]")

    def execute(self, logger: LoggingProtocol) -> None:
        self.logger = logger
        if len(self.subreddits) == 0:
            self.subreddits.extend(common_paths.iterate_subreddit_names(self.input_directory))
        for subreddit in self.subreddits:
            self.process_subreddit(subreddit)

    def process_subreddit(self, subreddit_name: str) -> None:
        self.post_message(f"Processing {subreddit_name}...")
        subreddit: Subreddit = self.load_subreddit(subreddit_name)
        with store.KeyValueStoreManager(common_paths.key_store_path(subreddit_name)) as store_mgr:
            key_store = store_mgr.store(subreddit_name)
            self.update_subreddit(subreddit, subreddit_name, key_store)
        self.save_subreddit(subreddit, subreddit_name)

    def update_subreddit(self, subreddit: Subreddit, subreddit_name: str, key_store: store.KeyValueStore) -> None: ...

    def load_subreddit(self, subreddit_name: str) -> Subreddit:
        input_filepath: Path = common_paths.posts_file(subreddit_name, self.input_directory)
        subreddit = Subreddit.from_msgpack_file(input_filepath, self.logger)
        return subreddit

    def save_subreddit(self, subreddit: Subreddit, subreddit_name: str) -> None:
        output_filepath: Path = common_paths.posts_file(subreddit_name, self.output_directory)
        subreddit.to_msgpack_file(output_filepath, self.logger)
