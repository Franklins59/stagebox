"""
Model mapping facade.

Loads a mapping from Shelly hardware model identifiers (hw_model) to
friendly model names from stagebox/data/shelly_model_map.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml


DEFAULT_MODEL_MAPPING: Dict[str, str] = {
    # Fallback / baseline entries (optional, can be kept minimal)
    "SHPLG-S": "Plug S",
    "SHPLG2-1": "Plug",
    "SHSW-1": "1PM",
    "SHSW-21": "2.5",
    "SHSW-PM": "1PM",
    "SHSW-L": "Dimmer",
}


def load_model_map(data_dir: Path) -> Dict[str, str]:
    """Load model mapping from shelly_model_map.yaml in the given data directory.

    If the file is missing or invalid, returns DEFAULT_MODEL_MAPPING.
    """
    mapping: Dict[str, str] = dict(DEFAULT_MODEL_MAPPING)

    map_path = data_dir / "shelly_model_map.yaml"
    if not map_path.exists():
        return mapping

    try:
        with map_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    mapping[k] = v
    except Exception:
        # On error, just fall back to defaults
        return mapping

    return mapping
