"""Domain exceptions with stable machine-readable categories."""


class DialogueLabError(ValueError):
    """Base exception for deterministic validation failures."""

    category = "dialogue_lab_error"


class CompatibilityError(DialogueLabError):
    """Raised when a canonical source is incompatible with this repository."""

    category = "compatibility_error"


class IdentifierError(DialogueLabError):
    """Raised when an identifier is malformed, duplicated, or unsafe to allocate."""

    category = "identifier_error"


class LifecycleError(DialogueLabError):
    """Raised when a lifecycle action is not allowed."""

    category = "lifecycle_error"


class GraphError(DialogueLabError):
    """Raised when the public-turn parent graph is invalid."""

    category = "graph_error"


class WriteSafetyError(DialogueLabError):
    """Raised when a requested canonical write violates safety policy."""

    category = "write_safety_error"


class StorageError(DialogueLabError):
    """Raised when local canonical storage is missing, incompatible, or corrupt."""

    category = "storage_error"
