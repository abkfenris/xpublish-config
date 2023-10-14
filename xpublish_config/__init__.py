"""Programmatic and overridable configuration loading for Xpublish."""
from .config import XpublishConfigManager

__all__ = ["XpublishConfigManager"]

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"
