"""
services/rec_service/mappings.py
Shared NCF user/item ID mappings for training and serving.
"""
from pathlib import Path
from typing import Optional

import structlog

from shared.config import settings
from training.id_mapping import load_mappings, resolve_user_key

log = structlog.get_logger(__name__)

USER_ID_MAP: dict[str, int] = {}
ITEM_ID_MAP: dict[str, int] = {}
REVERSE_ITEM_MAP: dict[int, str] = {}
N_USERS: int = 0
N_ITEMS: int = 0


def load_ncf_mappings() -> None:
    """Load persisted user/item mappings from disk."""
    global USER_ID_MAP, ITEM_ID_MAP, REVERSE_ITEM_MAP, N_USERS, N_ITEMS

    path = Path(settings.NCF_MAPPINGS_PATH)
    if not path.exists():
        log.warning("ncf_mappings.not_found", path=str(path))
        USER_ID_MAP = {}
        ITEM_ID_MAP = {}
        REVERSE_ITEM_MAP = {}
        N_USERS = 0
        N_ITEMS = 0
        return

    mappings = load_mappings(str(path))
    USER_ID_MAP = {str(k): int(v) for k, v in mappings.get("users", {}).items()}
    ITEM_ID_MAP = {str(k): int(v) for k, v in mappings.get("items", {}).items()}
    REVERSE_ITEM_MAP = {v: k for k, v in ITEM_ID_MAP.items()}
    N_USERS = mappings.get("n_users", len(USER_ID_MAP))
    N_ITEMS = mappings.get("n_items", len(ITEM_ID_MAP))
    log.info("ncf_mappings.loaded", n_users=N_USERS, n_items=N_ITEMS)


def resolve_user_index(user_id) -> Optional[int]:
    """Map a UUID or external user identifier to a model user index."""
    return USER_ID_MAP.get(resolve_user_key(user_id))


def resolve_item_index(isbn: str) -> Optional[int]:
    """Map an ISBN to a model item index."""
    return ITEM_ID_MAP.get(isbn)
