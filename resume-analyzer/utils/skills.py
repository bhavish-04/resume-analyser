"""
skills.py — Skill Loading and Extraction Module

Handles loading the predefined skills database from disk and matching
those skills against extracted text from resumes and job descriptions.
"""

import os
from typing import List, Set


# Resolve the path to skills_list.txt relative to this file's location,
# so the module works regardless of the working directory.
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_SKILLS_FILE = os.path.join(_DATA_DIR, "skills_list.txt")


def load_skills(filepath: str = _SKILLS_FILE) -> List[str]:
    """
    Load the predefined skills list from a text file.

    Each non-empty, non-comment line in the file is treated as one skill.
    Skills are normalized to lowercase and stripped of surrounding whitespace
    to ensure consistent matching.

    Args:
        filepath: Path to the skills text file. Defaults to
                  data/skills_list.txt relative to the project root.

    Returns:
        A list of lowercase skill strings.

    Raises:
        FileNotFoundError: If the skills file does not exist at the given path.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(
            f"Skills file not found at '{filepath}'. "
            f"Please ensure data/skills_list.txt exists."
        )

    skills = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip().lower()
            # Skip empty lines and comments
            if stripped and not stripped.startswith("#"):
                skills.append(stripped)

    return skills


def extract_skills(text: str, skills_list: List[str]) -> Set[str]:
    """
    Identify which skills from the predefined list appear in the given text.

    Matching is case-insensitive. For multi-word skills (e.g., "machine learning"),
    a substring search is used. For single-word skills, word-boundary matching
    prevents false positives (e.g., "r" should not match inside "react").

    Args:
        text:        The text to scan (resume or job description), already cleaned.
        skills_list: The list of skills to search for.

    Returns:
        A set of matched skill strings (lowercase).
    """
    import re

    text_lower = text.lower()
    found_skills: Set[str] = set()

    for skill in skills_list:
        # Multi-word skills: simple substring match is safe enough
        if " " in skill or "/" in skill or "." in skill:
            if skill in text_lower:
                found_skills.add(skill)
        else:
            # Single-word skills: use word-boundary regex to avoid partial matches
            # e.g., skill "r" should not match inside "react"
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_lower):
                found_skills.add(skill)

    return found_skills
