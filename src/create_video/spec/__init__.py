"""Ranh giới Python ↔ Remotion. Xem schema.json và validate.py."""

from .validate import SpecError, load, validate

__all__ = ["SpecError", "load", "validate"]
