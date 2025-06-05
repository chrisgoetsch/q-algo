# File: core/archetype_loader.py  (refactored)
"""Loads and validates setup archetypes used by mesh/brain agents.

Upgrades
--------
* Archetypes path configurable via `ARCHETYPES_FILE` env var.
* Structured JSON logging (core.logger_setup).
* LRU‑cached loader to avoid disk hits on every call.
* Graceful degradation if *jsonschema* is missing (warn, still load).
"""
from __future__ import annotations

import os, json
from functools import lru_cache
from typing import List, Dict

from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths / schema
# ---------------------------------------------------------------------------
ARCHETYPES_FILE = os.getenv("ARCHETYPES_FILE", "data/setup_archetypes.json")

_ARCHETYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "archetypes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["archetype_id", "pattern", "match_threshold"],
                "properties": {
                    "archetype_id": {"type": "string"},
                    "pattern": {"type": "object"},
                    "match_threshold": {"type": "number"},
                },
            },
        }
    },
    "required": ["archetypes"],
}

try:
    from jsonschema import validate, ValidationError  # type: ignore
except ImportError:  # soft‑dependency
    validate = None  # type: ignore
    ValidationError = Exception  # type: ignore
    logger.warning({"event": "jsonschema_missing", "msg": "Skipping schema validation"})

# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_archetypes() -> List[Dict]:
    """Return list of archetype dicts (cached). Empty list on failure."""
    if not os.path.exists(ARCHETYPES_FILE):
        logger.error({"event": "archetypes_file_missing", "path": ARCHETYPES_FILE})
        return []

    try:
        data = json.load(open(ARCHETYPES_FILE))

        if validate:
            validate(instance=data, schema=_ARCHETYPE_SCHEMA)  # type: ignore[arg-type]
        else:
            logger.debug({"event": "archetypes_no_validation"})

        archs = data.get("archetypes", [])
        logger.info({"event": "archetypes_loaded", "count": len(archs)})
        return archs

    except ValidationError as ve:  # type: ignore[misc]
        logger.error({"event": "archetypes_schema_fail", "err": ve.message})
        return []
    except Exception as e:
        logger.error({"event": "archetypes_load_fail", "err": str(e)})
        return []

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Loaded archetypes →", len(load_archetypes()))
