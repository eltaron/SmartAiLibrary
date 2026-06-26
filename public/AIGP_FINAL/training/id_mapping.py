"""
training/id_mapping.py
Stable user/item ID mappings for NCF training and serving.
"""
import json
from pathlib import Path
from typing import Any
from uuid import UUID


def build_user_mapping(user_ids: list[Any]) -> dict[str, int]:
    """Map user identifiers (UUID or str) to contiguous integer indices."""
    unique = sorted({str(uid) for uid in user_ids})
    return {uid: idx for idx, uid in enumerate(unique)}


def build_item_mapping(isbns: list[str]) -> dict[str, int]:
    """Map ISBNs to contiguous integer indices."""
    unique = sorted(set(isbns))
    return {isbn: idx for idx, isbn in enumerate(unique)}


def save_mappings(
    path: str,
    user_map: dict[str, int],
    item_map: dict[str, int],
) -> None:
    """Persist mappings alongside the trained model."""
    payload = {
        "users": user_map,
        "items": item_map,
        "n_users": len(user_map),
        "n_items": len(item_map),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def load_mappings(path: str) -> dict[str, Any]:
    """Load persisted user/item mappings."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_user_key(user_id: Any) -> str:
    """Normalise a user identifier to the mapping key format."""
    if isinstance(user_id, UUID):
        return str(user_id)
    return str(user_id)
