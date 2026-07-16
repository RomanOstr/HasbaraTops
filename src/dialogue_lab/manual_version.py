"""Operating Manual version parsing and compatibility checks."""

import re

from .errors import CompatibilityError
from .models import ManualVersion

VERSION_RE = re.compile(r"\bVersion\s+(\d+)\.(\d+)\b", re.IGNORECASE)


def parse_manual_version(text: str) -> ManualVersion:
    """Parse the first explicit Manual version marker from live text."""
    match = VERSION_RE.search(text)
    if match is None:
        raise CompatibilityError("Operating Manual version marker was not found")
    return ManualVersion(int(match.group(1)), int(match.group(2)), match.group(0))


def require_supported_manual(
    text: str,
    *,
    minimum: str = "2.7",
    supported_major: int = 2,
) -> tuple[ManualVersion, tuple[str, ...]]:
    """Return the live version and compatible-minor warnings or fail safely."""
    version = parse_manual_version(text)
    minimum_version = parse_manual_version(f"Version {minimum}")
    if version.major != supported_major:
        raise CompatibilityError(
            f"unsupported Manual major version {version.major}; "
            f"repository supports {supported_major}"
        )
    if version < minimum_version:
        raise CompatibilityError(
            f"Manual {version} is older than minimum supported version {minimum_version}"
        )
    warnings: tuple[str, ...] = ()
    if version.minor > minimum_version.minor:
        warnings = (f"Manual {version} is newer; revalidate repository compatibility",)
    return version, warnings
