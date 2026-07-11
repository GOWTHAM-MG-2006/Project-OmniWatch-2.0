"""
OmniWatch 2.0 — Config Drift Engine
Component: Package init with sanitization helpers
Layer: 7 (Cross-Cutting)
Phase: 3
Purpose: Input sanitization for subprocess safety in config drift integrators
"""

import re

VALID_ENTITY = re.compile(r'^[A-Za-z0-9_\-\.\/]+$')
VALID_CONFIG_VALUE = re.compile(r'^[A-Za-z0-9_\-\.\/\s\{\}\[\]"\':,=]+$')
VALID_COMMIT = re.compile(r'^[0-9a-f]{40}$')


def sanitize_entity(entity: str) -> str:
    """Sanitize entity name for safe subprocess use."""
    if not VALID_ENTITY.match(entity):
        raise ValueError(f"Invalid entity name: {entity!r}")
    return entity


def sanitize_config_value(value: str) -> str:
    """Sanitize config value for safe subprocess use."""
    if not VALID_CONFIG_VALUE.match(value):
        raise ValueError(f"Invalid config value: {value!r}")
    return value


def sanitize_commit(commit: str) -> str:
    """Sanitize Git commit SHA for safe subprocess use."""
    if commit and not VALID_COMMIT.match(commit):
        raise ValueError(f"Invalid commit SHA: {commit!r}")
    return commit
