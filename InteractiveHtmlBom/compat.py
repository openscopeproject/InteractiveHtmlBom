"""Compatibility utilities for optional wx dependency."""

import os

_wx = None


def should_create_wx_app():
    """Check if we should create a wx app based on environment."""
    return 'INTERACTIVE_HTML_BOM_NO_DISPLAY' not in os.environ


def get_wx():
    """Get the wx module, or None if not available."""
    global _wx
    if _wx is not None:
        return _wx
    try:
        import wx
        _wx = wx
        return _wx
    except ImportError:
        return None
