from typing import Annotated
from pydantic import BeforeValidator


def strip_whitespace(v: str) -> str:
    """Strip whitespace and validate non-empty string"""
    if isinstance(v, str):
        stripped = v.strip()
        if not stripped:
            raise ValueError("Cannot be empty or only whitespace")
        return stripped
    return v


def clean_tags(v: list[str] | None) -> list[str]:
    """Remove duplicates, empty strings, and strip whitespace from tags"""
    if v is None:
        return []
    cleaned = [tag.strip() for tag in v if tag and tag.strip()]
    return list(set(cleaned))


# Reusable type annotations
NonEmptyStr = Annotated[str, BeforeValidator(strip_whitespace)]
CleanTags = Annotated[list[str], BeforeValidator(clean_tags)]
