"""Deterministic revision identifiers for repository canonical documents."""

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str:
    """Return a stable content revision without printing or copying document bodies."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()
