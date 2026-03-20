from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

import rpg_subreddit_processor.utils.key_value_store as store
from rpg_subreddit_processor.entities import Subreddit
from rpg_subreddit_processor.utils import common_paths

from .base_reporting_command import BaseReportingCommand


class TextData(BaseModel):
    text: str


@dataclass
class ReportPotentialAcknowledgements(BaseReportingCommand):
    data: list[TextData] = field(default_factory=list)
    row_count: int = 9999

    def process(self, subreddit: Subreddit, subreddit_name: str, key_store: store.KeyValueStore) -> None:
        potentials: list[TextData]
        with key_store.txn() as txn:
            potentials = [
                TextData(text=node.get_text(txn))
                for node in subreddit.breadth_first_traversal()
                if (not node.is_root()) and node.author_id == node.get_root().author_id
            ]
        self.data.extend(potentials)

    def complete(self) -> None:
        file_path: Path = common_paths.potential_thanks_file()
        random.shuffle(self.data)
        rows_to_write = self.data[: self.row_count]
        with file_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps([item.model_dump() for item in rows_to_write], ensure_ascii=False, indent=2))
            f.write("\n")
