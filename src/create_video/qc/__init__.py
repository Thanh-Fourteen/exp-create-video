"""Bốn tầng QC. T1 chạy bằng code (chặn cứng), T2-T4 bằng model (đề xuất)."""

from .t1_technical import Check, run

__all__ = ["Check", "run"]
