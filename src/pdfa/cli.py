"""Command-line entry point for the pdfa project."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="pdfa",
        description="Skeleton CLI for interacting with AI backends.",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        default=None,
        help="Provide a prompt to send to the configured backend.",
    )
    return parser


def handle_prompt(prompt: str | None) -> int:
    """Handle the prompt argument and return an exit status code."""
    if prompt is None:
        print("No prompt provided. Use --prompt to supply one.")
        return 1

    print(f"Prompt received: {prompt}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return handle_prompt(args.prompt)


if __name__ == "__main__":
    sys.exit(main())
