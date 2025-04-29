# core/archetype_loader.py

import json
import logging
from jsonschema import validate, ValidationError

ARCHETYPES_FILE = "data/setup_archetypes.json"

ARCHETYPE_SCHEMA = {
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

def load_archetypes():
    try:
        with open(ARCHETYPES_FILE, "r") as f:
            data = json.load(f)

        validate(instance=data, schema=ARCHETYPE_SCHEMA)
        logging.info(f"Loaded and validated {len(data['archetypes'])} archetypes.")
        return data["archetypes"]

    except ValidationError as ve:
        logging.error(f"Archetype JSON validation failed: {ve.message}")
        return []

    except Exception as e:
        logging.error(f"Failed to load archetypes: {str(e)}", exc_info=True)
        return []

