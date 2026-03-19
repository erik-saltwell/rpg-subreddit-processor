# src/reddit_rpg_miner/cli/main.py

from __future__ import annotations

from datetime import datetime
from importlib.metadata import PackageNotFoundError, metadata
from importlib.metadata import version as dist_version

import typer
from dotenv import load_dotenv
from rich.console import Console

from rpg_subreddit_processor.arctic_shift import iter_subreddit_file_pairs, validate_arctic_shift_directory
from rpg_subreddit_processor.commands.prune_non_questions import PruneNonQuestions
from rpg_subreddit_processor.protocols import CompositeLogger, LoggingProtocol
from rpg_subreddit_processor.utils.common_paths import ProcessingStage
from rpg_subreddit_processor.utils.logging_config import configure_logging

from ..commands.convert_arctic_shift_data import ConvertArcticShiftData
from ..commands.dump_subreddit_text import DumpSubredditText
from .file_logging_protocol import FileLogger
from .rich_logging_protocol import RichConsoleLogger

load_dotenv()
configure_logging()

app = typer.Typer(
    name="rpg-subreddit-processor",
    add_completion=True,
    help="CLI for rpg-subreddit-processor",
)

LOG_FILENAME: str = "rpg_subreddit_processor.log"


def create_logger() -> LoggingProtocol:
    console = Console()
    console_logger: RichConsoleLogger = RichConsoleLogger(console)
    file_logger: FileLogger = FileLogger(LOG_FILENAME, verbose_training=True)
    return CompositeLogger([console_logger, file_logger])


def seconds_since(start: datetime) -> float:
    return (datetime.now() - start).total_seconds()


@app.command("test")
def test() -> None:
    """Simple smoke command."""
    console = Console()
    console.print("[green]Hello from test[/green]")


@app.command("convert-arctic-shift-data")
def convert_arctic_shift_data(
    subreddit: str | None = typer.Option(
        None,
        "--subreddit",
        "-s",
        help="Optional subreddit to process. If omitted, all discovered subreddits are processed.",
    ),
) -> None:
    """Covert arctic shift data to an inteernal json format."""
    validate_arctic_shift_directory()

    command = ConvertArcticShiftData()
    subreddits: list[str] = []
    if subreddit:
        subreddits.append(subreddit)
    else:
        subreddits.extend([pair.subreddit for pair in iter_subreddit_file_pairs()])

    command.subreddits = subreddits
    command.execute(create_logger())


@app.command("dump-subreddit-text")
def dump_subreddit_text(
    subreddit: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--subreddit",
        "-s",
        help="Optional subreddit(s) to process. Repeat to pass multiple. If omitted, all subreddits are processed.",
    ),
) -> None:
    """Load a subreddit's msgpack file and print all node text to stdout."""
    command = DumpSubredditText(input_stage=ProcessingStage.Converted)
    if subreddit:
        command.subreddits.extend(subreddit)
    command.execute(create_logger())


@app.command("prune-non-questions")
def prune_non_questions(
    subreddit: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--subreddit",
        "-s",
        help="Optional subreddit(s) to process. Repeat to pass multiple. If omitted, all subreddits are processed.",
    ),
) -> None:
    command = PruneNonQuestions(
        input_stage=ProcessingStage.Converted,
        output_stage=ProcessingStage.NonQuestionsPruned,
    )
    if subreddit:
        command.subreddits.extend(subreddit)
    command.execute(create_logger())


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if not value:
        return

    # IMPORTANT: distribution name (pyproject.toml [project].name), often hyphenated.
    # Example: "my-tool" even if your import package is "my_tool".
    DIST_NAME = "rpg-subreddit-processor"

    console = Console()

    try:
        pkg_version = dist_version(DIST_NAME)
        md = metadata(DIST_NAME)
        try:
            pkg_name = md["Name"]
        except KeyError:
            pkg_name = DIST_NAME

        console.print(f"{pkg_name} {pkg_version}")
    except PackageNotFoundError:
        # Running from source without an installed distribution
        console.print(f"{DIST_NAME} 0.0.0+unknown")

    raise typer.Exit()


@app.callback()
def _callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Root command group for reddit_rpg_miner."""
    # Intentionally empty: this forces Typer to keep subcommands like `test`.
    pass


if __name__ == "__main__":
    app()
