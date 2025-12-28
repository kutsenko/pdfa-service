# CLAUDE.md - Quick Reference for AI Agents

**Single Source of Truth**: All development guidelines are in **[AGENTS.md](AGENTS.md)**

This file provides only the essential quick-start commands. For everything else, see [AGENTS.md](AGENTS.md).

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before Every Commit

```bash
pytest                      # All tests must pass
black src tests             # Format code
ruff check src tests --fix  # Lint and fix
```

## Key Principles

1. **TDD Required**: Write tests BEFORE production code (RED → GREEN → REFACTOR)
2. **AGENTS.md is Single Source of Truth**: Read it for all development guidelines
3. **English Only**: All code, comments, commits in English
4. **Both CLI and API use `convert_to_pdfa()`**: Never duplicate logic

---

**For all details, see [AGENTS.md](AGENTS.md)**
