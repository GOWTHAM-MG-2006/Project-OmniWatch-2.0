"""Query validation utilities for safe SQL execution."""
import re

BLOCKED_KEYWORDS = frozenset([
    "DROP", "DELETE", "ALTER", "TRUNCATE", "INSERT", "UPDATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
])

ALLOWED_PATTERNS = [
    re.compile(r'^\s*SELECT\b', re.IGNORECASE),
    re.compile(r'^\s*SHOW\b', re.IGNORECASE),
    re.compile(r'^\s*DESCRIBE\b', re.IGNORECASE),
    re.compile(r'^\s*EXPLAIN\b', re.IGNORECASE),
]

def validate_query(query: str) -> bool:
    query_upper = query.upper().strip()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf'\b{keyword}\b', query_upper):
            return False
    for pattern in ALLOWED_PATTERNS:
        if pattern.match(query):
            return True
    return False

def validate_view_name(name: str) -> bool:
    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name))

def validate_parquet_path(path: str) -> bool:
    if '..' in path:
        return False
    sensitive = ['/etc', '/proc', '/sys', '/dev']
    for s in sensitive:
        if path.startswith(s):
            return False
    return True
