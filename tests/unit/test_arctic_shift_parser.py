from __future__ import annotations

from pathlib import Path

import pytest

from rpg_subreddit_processor.arctic_shift import iter_subreddit_file_pairs
from rpg_subreddit_processor.arctic_shift.arctic_shift_parser import _validate_subreddit_file_pairs_internal


def _create_files(base: Path, subreddit_files: dict[str, list[str]]) -> None:
    """Create files under per-subreddit subdirectories: base/<sub>/<filename>."""
    for sub, filenames in subreddit_files.items():
        sub_dir = base / sub
        sub_dir.mkdir(exist_ok=True)
        for name in filenames:
            (sub_dir / name).touch()


class TestIterSubredditFilePairs:
    def test_matched_pairs(self, tmp_path: Path) -> None:
        _create_files(
            tmp_path,
            {
                "DnD": ["r_DnD_posts.jsonl", "r_DnD_comments.jsonl"],
                "osr": ["r_osr_posts.jsonl", "r_osr_comments.jsonl"],
            },
        )
        result = list(iter_subreddit_file_pairs(tmp_path))
        assert len(result) == 2
        assert result[0] == ("DnD", tmp_path / "DnD" / "r_DnD_posts.jsonl", tmp_path / "DnD" / "r_DnD_comments.jsonl")
        assert result[1] == ("osr", tmp_path / "osr" / "r_osr_posts.jsonl", tmp_path / "osr" / "r_osr_comments.jsonl")

    def test_sorted_order(self, tmp_path: Path) -> None:
        _create_files(
            tmp_path,
            {
                "zzz": ["r_zzz_posts.jsonl", "r_zzz_comments.jsonl"],
                "aaa": ["r_aaa_posts.jsonl", "r_aaa_comments.jsonl"],
            },
        )
        result = list(iter_subreddit_file_pairs(tmp_path))
        names = [name for name, _, _ in result]
        assert names == ["aaa", "zzz"]

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = list(iter_subreddit_file_pairs(tmp_path))
        assert result == []

    def test_posts_without_comments_raises(self, tmp_path: Path) -> None:
        _create_files(tmp_path, {"DnD": ["r_DnD_posts.jsonl"]})
        posts_subreddits = {"DnD": tmp_path / "DnD" / "r_DnD_posts.jsonl"}
        comments_subreddits: dict[str, Path] = {}
        with pytest.raises(ValueError, match="Posts file without matching comments"):
            _validate_subreddit_file_pairs_internal(posts_subreddits, comments_subreddits)

    def test_comments_without_posts_raises(self, tmp_path: Path) -> None:
        _create_files(tmp_path, {"DnD": ["r_DnD_comments.jsonl"]})
        posts_subreddits: dict[str, Path] = {}
        comments_subreddits = {"DnD": tmp_path / "DnD" / "r_DnD_comments.jsonl"}
        with pytest.raises(ValueError, match="Comments file without matching posts"):
            _validate_subreddit_file_pairs_internal(posts_subreddits, comments_subreddits)

    def test_mixed_mismatch_raises(self, tmp_path: Path) -> None:
        _create_files(
            tmp_path,
            {
                "DnD": ["r_DnD_posts.jsonl", "r_DnD_comments.jsonl"],
                "osr": ["r_osr_posts.jsonl"],
                "gurps": ["r_gurps_comments.jsonl"],
            },
        )
        posts_subreddits = {
            "DnD": tmp_path / "DnD" / "r_DnD_posts.jsonl",
            "osr": tmp_path / "osr" / "r_osr_posts.jsonl",
        }
        comments_subreddits = {
            "DnD": tmp_path / "DnD" / "r_DnD_comments.jsonl",
            "gurps": tmp_path / "gurps" / "r_gurps_comments.jsonl",
        }
        with pytest.raises(ValueError, match="Mismatched subreddit files") as exc_info:
            _validate_subreddit_file_pairs_internal(posts_subreddits, comments_subreddits)
        msg = str(exc_info.value)
        assert "r_osr_posts.jsonl" in msg
        assert "r_gurps_comments.jsonl" in msg

    def test_iter_subreddit_file_pairs_uses_validation(self, tmp_path: Path) -> None:
        _create_files(tmp_path, {"DnD": ["r_DnD_posts.jsonl"]})
        with pytest.raises(ValueError, match="Posts file without matching comments"):
            list(iter_subreddit_file_pairs(tmp_path))

    def test_subreddit_dirs_without_arctic_shift_files_are_skipped(self, tmp_path: Path) -> None:
        """Dirs at later processing stages (no arctic shift files) are silently ignored."""
        _create_files(
            tmp_path,
            {
                "osr": ["r_osr_posts.jsonl", "r_osr_comments.jsonl"],
                "bladesinthedark": ["initial_subreddit_trees.msgpack"],
            },
        )
        result = list(iter_subreddit_file_pairs(tmp_path))
        assert len(result) == 1
        assert result[0].subreddit == "osr"
