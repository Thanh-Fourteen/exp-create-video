"""`out/<id>/state.json` — một file, do CODE ghi, cho mọi vai trong team.

Ba việc, không hơn (research/10-team.md §2, P4.S0):

1. **Chạy lại tiếp từ chỗ hỏng.** Mỗi stage ghi hash đầu vào + artifact sinh ra.
   Lần sau, stage nào `done`, hash trùng và artifact còn trên đĩa thì bỏ qua.
2. **Biết mình tốn bao nhiêu.** Mọi lần gọi LLM vào `llm_calls[]` (token, thời
   gian, cost) — kể cả lần fail. Chi phí 0đ phụ thuộc chính sách auth (research/10
   §1), nên con số này là thứ duy nhất cho biết mình đang dùng bao nhiêu.
3. **Ghi lỗi** vào `errors[]` thay vì chỉ in ra terminal rồi mất.

Cố ý KHÔNG phải framework: không DAG, không đăng ký stage, không plugin. Bẫy của
step là "càng nhiều tầng điều phối càng nhiều chỗ lệch".
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def hash_inputs(*parts: Any) -> str:
    """sha256 của đầu vào một stage.

    `Path` → băm NỘI DUNG file (đổi rubric là đổi hash), không băm đường dẫn.
    Còn lại → JSON chuẩn hoá `sort_keys`, nên dict cùng nội dung khác thứ tự
    vẫn ra cùng hash. Thứ không JSON được thì rơi về `str()` — đủ cho số/enum.
    """
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, Path):
            h.update(b"file:" + str(p.name).encode())
            h.update(p.read_bytes() if p.exists() else b"<missing>")
        else:
            h.update(json.dumps(p, sort_keys=True, ensure_ascii=False, default=str).encode())
        h.update(b"\x00")
    return h.hexdigest()[:16]


@dataclass
class StageRecord:
    status: str = "pending"            # pending | running | done | failed
    input_hash: str = ""
    outputs: list[str] = field(default_factory=list)   # tương đối so với out/<id>/
    started_at: str = ""
    finished_at: str = ""
    wall_sec: float = 0.0


@dataclass
class State:
    video_id: str
    dir: Path
    stage: str = ""                    # stage đang/vừa chạy
    round: int = 0                     # vòng QC (P4.S4); 0 = trước QC
    stages: dict[str, StageRecord] = field(default_factory=dict)
    llm_calls: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    _t0: dict[str, float] = field(default_factory=dict, repr=False)

    # ── đọc / ghi ───────────────────────────────────────────────────────────
    @property
    def path(self) -> Path:
        return self.dir / "state.json"

    @classmethod
    def load(cls, out_dir: Path, video_id: str | None = None) -> "State":
        out_dir = Path(out_dir)
        p = out_dir / "state.json"
        if not p.exists():
            return cls(video_id=video_id or out_dir.name, dir=out_dir)
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            video_id=d.get("video_id", video_id or out_dir.name),
            dir=out_dir,
            stage=d.get("stage", ""),
            round=int(d.get("round", 0)),
            stages={k: StageRecord(**v) for k, v in d.get("stages", {}).items()},
            llm_calls=d.get("llm_calls", []),
            errors=d.get("errors", []),
        )

    def save(self) -> None:
        """Ghi tạm rồi `os.replace` — bị kill giữa lúc ghi thì file cũ vẫn nguyên.

        Đây chính là kịch bản mà state.json sinh ra để xử lý; một state.json
        cụt nửa chừng sẽ làm lần chạy lại hỏng theo kiểu khó hiểu hơn cả lỗi gốc.
        """
        self.dir.mkdir(parents=True, exist_ok=True)
        d = {
            "video_id": self.video_id,
            "stage": self.stage,
            "round": self.round,
            "stages": {k: asdict(v) for k, v in self.stages.items()},
            "llm_calls": self.llm_calls,
            "errors": self.errors,
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    # ── stage ───────────────────────────────────────────────────────────────
    def is_fresh(self, stage: str, input_hash: str) -> bool:
        """Bỏ qua được không: `done` + hash trùng + MỌI artifact còn trên đĩa."""
        r = self.stages.get(stage)
        if r is None or r.status != "done" or r.input_hash != input_hash:
            return False
        return all((self.dir / o).exists() for o in r.outputs)

    def begin(self, stage: str, input_hash: str) -> None:
        self.stage = stage
        self._t0[stage] = time.time()
        self.stages[stage] = StageRecord(status="running", input_hash=input_hash, started_at=_now())
        self.save()

    def done(self, stage: str, outputs: list[Path | str] = ()) -> None:
        r = self.stages[stage]
        r.status = "done"
        r.outputs = [self._rel(o) for o in outputs]
        r.finished_at = _now()
        r.wall_sec = round(time.time() - self._t0.pop(stage, time.time()), 2)
        self.save()

    def fail(self, stage: str, exc: BaseException) -> None:
        r = self.stages.setdefault(stage, StageRecord())
        # Lỗi nảy ra SAU khi stage đã xong (vd. kiểm độ dài audio sau TTS) không
        # được xoá kết quả của nó — chỉ ghi lỗi, giữ cache.
        if r.status != "done":
            r.status = "failed"
            r.finished_at = _now()
        self.errors.append({"stage": stage, "at": _now(), "type": type(exc).__name__, "msg": str(exc)[:2000]})
        self.save()

    def _rel(self, p: Path | str) -> str:
        p = Path(p)
        try:
            return str(p.resolve().relative_to(self.dir.resolve()))
        except ValueError:
            return str(p)

    # ── LLM ─────────────────────────────────────────────────────────────────
    def log_llm_call(self, rec: dict) -> None:
        self.llm_calls.append({"stage": self.stage, "round": self.round, "at": _now(), **rec})
        self.save()
