"""Agent. Chỉ dùng LLM ở chỗ cần suy luận: kịch bản, trend, critic."""

from .scriptwriter import Script, Shot, write_script, write_script_sync

__all__ = ["Script", "Shot", "write_script", "write_script_sync"]
