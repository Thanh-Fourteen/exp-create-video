"""Xương sống team (P4.S0): `run_role` + `state.json`. Xem research/10-team.md §1–2."""

from .role import RoleError, arun_role, run_role
from .state import State, hash_inputs

__all__ = ["RoleError", "State", "arun_role", "hash_inputs", "run_role"]
