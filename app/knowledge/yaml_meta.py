from __future__ import annotations

import yaml


def parse_card_yaml(block: str) -> dict:
    """Parse distill-era card YAML frontmatter."""
    if not block.strip():
        return {}
    data = yaml.safe_load(block)
    return data if isinstance(data, dict) else {}
