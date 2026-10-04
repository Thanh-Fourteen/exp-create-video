"""Worker (W2, 2026-10-02): MỘT job một lúc, pipeline chạy trong process group riêng.

    .venv/bin/python -m create_video.web.worker            # chạy mãi (systemd user service)
    .venv/bin/python -m create_video.web.worker --once     # một job rồi thoát (test)

Vì sao tự viết, không Huey/Celery (research/12 §1, research/probes/w2-research.md): cần HUỶ job đang chạy
(Huey `revoke()` không dừng được job đang chạy) và chạy tiếp sau crash; hàng đợi giữ trong SQLite, không RAM.

Một job đi 1–2 lượt:
- `phase=script` (job có cổng duyệt): pipeline `--stop-after script` (~5 phút, 0 GPU) → `awaiting_approval`.
- `phase=full`: pipeline `--qc` tới mp4 + `result.json` → `done`. Kịch bản đã có thì pipeline dùng lại.

Bị kill / máy sập giữa chừng → khởi động lại thì job 'running' quá hạn heartbeat được xếp lại hàng; pipeline
nối tiếp từ `state.json` (stage xong + hash trùng thì bỏ qua) — không mất phần đã làm.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import db

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = REPO_ROOT / "out"
LOG_DIR = REPO_ROOT / "exp" / "web" / "logs"
PY = REPO_ROOT / ".venv" / "bin" / "python"

HEARTBEAT_SEC = 5
LEASE_SEC = 120
TERM_GRACE_SEC = 20
# Cửa vào bước nặng (đo 2026-10-02): FLUX/VLM đỉnh ~1,8–3 GB VRAM; máy từng sập vì RAM khi chạy chồng việc.
MIN_GPU_FREE_MIB = 3000
MIN_RAM_FREE_GB = 8.0
ADMIT_WAIT_SEC = 60


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def gpu_free_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def ram_free_gb() -> float:
    import psutil

    return psutil.virtual_memory().available / 2**30


def machine() -> dict:
    import psutil

    vm = psutil.virtual_memory()
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
        used, total, util = (int(x) for x in q.strip().splitlines()[0].split(","))
    except Exception:
        used = total = util = None
    du = shutil.disk_usage(OUT)
    return {"gpu_used_mib": used, "gpu_total_mib": total, "gpu_util": util,
            "ram_used_gb": round((vm.total - vm.available) / 2**30, 1), "ram_total_gb": round(vm.total / 2**30, 1),
            "disk_free_gb": round(du.free / 2**30, 1)}


def admit(job: dict) -> str | None:
    """None = được chạy; chuỗi = lý do phải đợi. Lượt `script` không dùng GPU nên chỉ kiểm RAM."""
    if ram_free_gb() < MIN_RAM_FREE_GB:
        return f"RAM chỉ còn {ram_free_gb():.1f} GB (cần ≥ {MIN_RAM_FREE_GB:.0f})"
    if job["phase"] == "full":
        free = gpu_free_mib()
        if free is not None and free < MIN_GPU_FREE_MIB:
            return f"GPU chỉ còn {free} MiB trống — dự án khác đang dùng (cần ≥ {MIN_GPU_FREE_MIB})"
    return None


def _prepare_revoice(job: dict) -> None:
    """Đổi giọng: chép kịch bản + hình + nhạc của video gốc sang thư mục mới → pipeline chỉ chạy lại
    giọng → spec → dựng → QC (~8 phút thay vì ~25)."""
    src = OUT / job["source"] if job.get("source") else None
    dst = OUT / job["video_id"]
    if src is None or dst.exists():
        return
    dst.mkdir(parents=True)
    for name in ("brief.json", "script.json"):
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    for d in ("gen", "shots", "depth-gen"):
        if (src / d).exists():
            shutil.copytree(src / d, dst / d)
    if (src / "audio" / "music_ace.wav").exists():
        (dst / "audio").mkdir()
        shutil.copy2(src / "audio" / "music_ace.wav", dst / "audio" / "music_ace.wav")


def command(job: dict) -> list[str]:
    topic = job["topic"]
    cmd = [str(PY), "-m", "create_video.pipeline", topic, "--id", job["video_id"], "--visual", "flux2",
           "--duration", str(job["duration"]), "--voice", job["voice"]]
    if job["phase"] == "script":
        cmd += ["--stop-after", "script"]
    else:
        cmd += ["--qc"]
    return cmd


def _env() -> dict:
    env = dict(os.environ)
    # PATH của systemd user rất ngắn — pipeline cần ffmpeg (miniconda), nvidia-smi, node (render).
    env["PATH"] = ":".join([str(REPO_ROOT / ".venv" / "bin"), str(Path.home() / ".local" / "bin"),
                            "/home/tony/miniconda3/bin",
                            "/usr/local/bin", "/usr/bin", "/bin", env.get("PATH", "")])
    env.setdefault("HOME", str(Path.home()))
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _kill(proc: subprocess.Popen) -> None:
    """SIGTERM cả process group (pipeline + mọi tiến trình con: aligner, FLUX, Chrome render), đợi, rồi SIGKILL.
    Process chết là driver CUDA nhả VRAM của nó."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(TERM_GRACE_SEC)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


_CURRENT: dict = {}


def _install_sigterm() -> None:
    """systemd stop (KillMode=mixed gửi SIGTERM cho worker trước): dừng job sạch, trả về hàng đợi —
    lần khởi động sau pipeline nối tiếp từ cache."""
    def h(signum, frame):
        p, jid = _CURRENT.get("proc"), _CURRENT.get("id")
        if p is not None and p.poll() is None:
            _kill(p)
            db.update_job(jid, state="queued", pid=None, attempts=max(0, _CURRENT.get("attempts", 1) - 1))
            log(f"↩ dừng worker — trả {jid} về hàng đợi")
        sys.exit(0)

    signal.signal(signal.SIGTERM, h)


def run_job(job: dict) -> str:
    """Chạy một lượt của job. Trả trạng thái cuối của lượt: awaiting_approval | done | failed | cancelled."""
    jid = job["id"]
    if job["kind"] == "revoice":
        _prepare_revoice(job)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logf = open(LOG_DIR / f"{jid}.log", "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} phase={job['phase']} attempt={job['attempts']}\n")
    logf.flush()
    proc = subprocess.Popen(command(job), cwd=REPO_ROOT, stdout=logf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True, env=_env())
    db.update_job(jid, pid=proc.pid, heartbeat_at=time.time())
    _CURRENT.update(proc=proc, id=jid, attempts=job["attempts"])
    log(f"▶ {jid} {job['video_id']} phase={job['phase']} pid={proc.pid}")
    cancelled = False
    while proc.poll() is None:
        time.sleep(HEARTBEAT_SEC)
        db.update_job(jid, heartbeat_at=time.time())
        cur = db.get_job(jid)
        if cur and cur["cancel_requested"]:
            log(f"✗ huỷ {jid}")
            _kill(proc)
            cancelled = True
    logf.close()
    _CURRENT.clear()
    out_dir = OUT / job["video_id"]
    st = json.loads((out_dir / "state.json").read_text(encoding="utf-8")) if (out_dir / "state.json").exists() else {}
    if cancelled:
        new, err = "cancelled", None
    elif job["phase"] == "script" and st.get("stage") == "awaiting_approval" and proc.returncode == 0:
        new, err = "awaiting_approval", None
    elif job["phase"] == "full" and (out_dir / "result.json").exists():
        new, err = "done", None
    else:
        errs = st.get("errors") or []
        err = (errs[-1]["msg"] if errs else f"pipeline thoát mã {proc.returncode}")[:1500]
        tail = (LOG_DIR / f"{jid}.log").read_text(encoding="utf-8", errors="replace")[-4000:]
        if "Login expired" in tail or "Invalid API key" in tail or "/login" in tail:
            err = "Claude chưa đăng nhập / phiên hết hạn — chạy `claude` trên máy tony rồi /login, sau đó bấm Chạy lại"
        new = "failed"
    db.update_job(jid, state=new, pid=None, error=err,
                  finished_at=time.time() if new in ("done", "failed", "cancelled") else None)
    if new == "awaiting_approval" and night_auto_ok():
        # W5: chạy đêm — tự duyệt kịch bản (nguồn đã qua cổng code của researcher; QC T4 vẫn CHẶN mâu thuẫn
        # sự thật ở lượt full, video không bao giờ tự đăng). w5-research.md §4.
        db.approve(jid)
        db.update_job(jid, auto_approved=1)
        log(f"☾ tự duyệt (chạy đêm) {jid}")
        return "queued"
    log(f"■ {jid} → {new}{(' · ' + err[:120]) if err else ''}")
    return new


def _night() -> dict:
    return db.kv_get("night", {}) or {}


def in_night(now: float | None = None) -> bool:
    n = _night()
    if not n.get("enabled"):
        return False
    h = time.localtime(now or time.time()).tm_hour
    s, e = int(n.get("start", 23)), int(n.get("end", 6))
    return (s <= h or h < e) if s > e else (s <= h < e)


def night_auto_ok() -> bool:
    """Trong khung đêm và chưa quá số video tự duyệt cho phép trong 12 giờ qua."""
    if not in_night():
        return False
    recent = [j for j in db.list_jobs(("queued", "running", "done", "failed"))
              if j.get("auto_approved") and j["created_at"] > time.time() - 12 * 3600]
    return len(recent) < int(_night().get("max", 4))


_TREND = {"proc": None}
TREND_HOUR = 6        # 6:30 sáng: gợi ý chủ đề mới cho trang Tạo video


def daily_trends() -> None:
    """Chạy trend scout một lần mỗi sáng (không GPU) — process riêng, KHÔNG chặn hàng đợi video."""
    p = _TREND["proc"]
    if p is not None:
        if p.poll() is None:
            return
        log(f"✓ trend scout xong (mã {p.returncode})")
        _TREND["proc"] = None
    now = time.localtime()
    today = time.strftime("%Y-%m-%d", now)
    if (now.tm_hour, now.tm_min) < (TREND_HOUR, 30) or db.kv_get("trend_date") == today:
        return
    if list((REPO_ROOT / "team" / "trends").glob(f"{today}-*.json")):
        db.kv_set("trend_date", today)
        return
    db.kv_set("trend_date", today)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    f = open(LOG_DIR / f"trend-{today}.log", "a", encoding="utf-8")
    _TREND["proc"] = subprocess.Popen([str(PY), "-m", "create_video.team.trend_scout", "--slot", "am"], cwd=REPO_ROOT,
                                      stdout=f, stderr=subprocess.STDOUT, start_new_session=True, env=_env())
    log("▶ trend scout buổi sáng")


def loop(once: bool = False) -> None:
    db.init()
    _install_sigterm()
    # Chỉ có MỘT worker → lúc khởi động, mọi job 'running' đều là mồ côi của lần chạy trước (lease = 0).
    for j in db.stale_running(0):                # process cũ còn sống (worker chết, job thì không) → giết trước
        if j.get("pid"):
            try:
                os.killpg(j["pid"], signal.SIGTERM)
                log(f"✗ giết process group mồ côi {j['pid']} của {j['id']}")
            except (ProcessLookupError, PermissionError):
                pass
    back = db.recover_stale(0)
    if back:
        log(f"↻ xếp lại {len(back)} job dở: {', '.join(back)}")
    log("worker sẵn sàng")
    waiting_reason = None
    while True:
        job = db.claim_next()
        if job is None:
            if once:
                return
            try:
                daily_trends()
            except Exception as e:
                log(f"⚠ việc buổi sáng lỗi: {e}")
            time.sleep(3)
            continue
        why = admit(job)
        if why:
            # trả lại hàng, đợi; báo lý do lên web qua cột error (không phải lỗi thật)
            db.update_job(job["id"], state="queued", error=f"đợi: {why}", attempts=job["attempts"] - 1)
            if why != waiting_reason:
                log(f"… {job['id']} đợi: {why}")
                waiting_reason = why
            time.sleep(ADMIT_WAIT_SEC)
            continue
        waiting_reason = None
        run_job(job)
        if once:
            return


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="worker xưởng video — 1 job một lúc")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args(argv)
    loop(once=a.once)
    return 0


if __name__ == "__main__":
    sys.exit(main())
