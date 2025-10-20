# pdfa

Skeleton for a Python CLI project designed to interact with multiple AI backends.

## Features

- Source code located under `src/` with an importable package named `pdfa`.
- Basic CLI entry point that can be executed with `python -m pdfa.cli` or the `pdfa` console script after installation.
- Testing scaffold using `pytest`.
- Tooling configuration for `black` and `ruff` to keep code formatted and linted.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pdfa --help
pytest
```

## Project Layout

```
.
├── pyproject.toml
├── README.md
├── src
│   └── pdfa
│       ├── __init__.py
│       └── cli.py
└── tests
    ├── __init__.py
    └── test_cli.py
```
