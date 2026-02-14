"""Utility modules for syntek-security-core.

This package contains utility functions and classes for security-core,
including performance metrics tracking, request utilities, and helpers.
"""

from __future__ import annotations

__all__ = ["PerformanceMetrics"]

try:
    from .performance_metrics import PerformanceMetrics
except ImportError:
    # Allow graceful degradation if dependencies not available
    PerformanceMetrics = None  # type: ignore[assignment, misc]
