"""Prompt and config loader for pipeline agents.

Reads prompt text and configuration from external files so that
they can be edited without touching Python code.
"""

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    """Load a prompt text file by name (without extension)."""
    path = _PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


@lru_cache
def load_known_techs() -> list[str]:
    """Load the known technologies list (one per line)."""
    path = _PROMPTS_DIR / "known_techs.txt"
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
