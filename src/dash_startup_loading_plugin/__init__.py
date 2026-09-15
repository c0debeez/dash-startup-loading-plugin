"""Full-screen startup loading overlay for Dash applications."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dash-startup-loading-plugin")
except PackageNotFoundError:  # pragma: no cover - source tree fallback
    __version__ = "1.1.0"

from .plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)

__all__ = [
    "StartupLoadingConfig",
    "__version__",
    "setup",
    "get_config",
    "reset_config",
]
