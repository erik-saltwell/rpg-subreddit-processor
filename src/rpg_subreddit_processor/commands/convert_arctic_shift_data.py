from collections.abc import Iterator
from pathlib import Path

import rpg_subreddit_processor.utils.common_paths as common_paths
import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.arctic_shift.arctic_shift_parser import (
    _create_nodes_from_arctic_shift_data,
    comments_file_from_subreddit_name,
    posts_file_from_subreddit_name,
)
from rpg_subreddit_processor.entities import RedditNode, Subreddit
from rpg_subreddit_processor.protocols import CommmandProtocol, LoggingProtocol
from rpg_subreddit_processor.protocols.logging_protocol import NullLogger


class ConvertArcticShiftData(CommmandProtocol):
    subreddits: list[str]
    logger: LoggingProtocol = NullLogger()

    def post_message(self, message: str) -> None:
        self.logger.report_message("[blue]" + message + "[/blue]")

    def execute(self, logger: LoggingProtocol) -> None:
        self.logger = logger
        for subdreddit in self.subreddits:
            self.convert_subreddit(subdreddit)

    def convert_subreddit(self, subreddit_name: str) -> None:
        self.post_message(f"Converting {subreddit_name}...")
        with self.logger.status("Loading...") as status:
            posts_filepath: Path = posts_file_from_subreddit_name(subreddit_name)
            comments_filepath: Path = comments_file_from_subreddit_name(subreddit_name)
            with store.KeyValueStoreManager(common_paths.key_store_path(subreddit_name)) as store_mgr:
                key_store: store.KeyValueStore = store_mgr.store(subreddit_name)
                with key_store.txn() as txn:
                    nodes: Iterator[RedditNode] = _create_nodes_from_arctic_shift_data(
                        posts_filepath, comments_filepath, txn
                    )
                    status.update("Building tree...")
                    subreddit: Subreddit = Subreddit.from_node_list(nodes, subreddit_name)
                    status.update("Saving...")
                    subreddit.to_json_file(
                        common_paths.initial_subreddit_path(subreddit_name) / Path(subreddit_name + "_posts.json")
                    )
