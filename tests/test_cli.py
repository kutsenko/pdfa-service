"""Tests for the pdfa CLI skeleton."""

from pdfa import __version__
from pdfa import cli


def test_version() -> None:
    """Ensure the package exposes a version string."""
    assert __version__ == "0.1.0"


def test_handle_prompt_when_prompt_missing(capsys) -> None:
    """CLI should instruct the user to provide a prompt when none is supplied."""
    exit_code = cli.handle_prompt(None)

    captured = capsys.readouterr()
    assert "No prompt provided" in captured.out
    assert exit_code == 1


def test_handle_prompt_success(capsys) -> None:
    """CLI should echo the prompt for now as a placeholder behaviour."""
    exit_code = cli.handle_prompt("Hello!")

    captured = capsys.readouterr()
    assert "Prompt received: Hello!" in captured.out
    assert exit_code == 0
