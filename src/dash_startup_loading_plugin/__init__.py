"""Full-screen startup loading overlay for Dash applications."""

from .plugin import (
    StartupLoadingConfig,
    __version__,
    get_config,
    reset_config,
    setup,
)

__all__ = [
    "StartupLoadingConfig",
    "__version__",
    "get_config",
    "reset_config",
    "setup",
]
