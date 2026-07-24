"""Domain exceptions with stable machine-readable categories."""


class HasbaraTopsError(ValueError):
    """Base exception for deterministic validation failures."""

    category = "hasbaratops_error"


class CompatibilityError(HasbaraTopsError):
    """Raised when a canonical source is incompatible with this repository."""

    category = "compatibility_error"


class IdentifierError(HasbaraTopsError):
    """Raised when an identifier is malformed, duplicated, or unsafe to allocate."""

    category = "identifier_error"


class LifecycleError(HasbaraTopsError):
    """Raised when a lifecycle action is not allowed."""

    category = "lifecycle_error"


class GraphError(HasbaraTopsError):
    """Raised when the public-turn parent graph is invalid."""

    category = "graph_error"


class WriteSafetyError(HasbaraTopsError):
    """Raised when a requested canonical write violates safety policy."""

    category = "write_safety_error"


class StorageError(HasbaraTopsError):
    """Raised when local canonical storage is missing, incompatible, or corrupt."""

    category = "storage_error"
