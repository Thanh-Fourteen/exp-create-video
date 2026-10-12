"""Canh web (2026-10-09): web treo im lặng 2 lần (06/10, 09/10) — trang động không trả lời, file tĩnh vẫn trả.

    python -m create_video.web.watchdog        # xuong-watchdog.timer gọi mỗi phút

Gọi `/p/machine` (trang động nhẹ nhất). Treo 2 lần LIỀN → `kill -USR1` (faulthandler in ngăn xếp mọi luồng ra journal để
tìm gốc) rồi restart xuong-web. KHÔNG restart khi ổ đĩa nghẽn (`/proc/pressure/io` some avg10 > 30): lúc đó web chậm vì
job nạp model, restart chỉ làm tệ hơn (memory xuong-web-treo).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

URL = "http://127.0.0.1:8770/p/machine"
STATE = Path(__file__).resolve().parents[3] / "exp" / "web" / "watchdog.json"
TIMEOUT_SEC = 20
FAILS_TO_RESTART = 2
IO_BUSY = 30.0


def ok() -> bool:
    req = urllib.request.Request(URL, headers={"Tailscale-User-Login": os.environ.get("XUONG_WATCH_USER", "thanh-fourteen@github")})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            return r.status == 200
    except Exception:
        return False


def io_busy() -> float:
    try:
        line = Path("/proc/pressure/io").read_text().splitlines()[0]
        return float(line.split("avg10=")[1].split()[0])
    except Exception:
        return 0.0


def web_pid() -> int | None:
    out = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", "xuong-web"],
                         capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() and out != "0" else None


def main() -> int:
    st = json.loads(STATE.read_text()) if STATE.exists() else {"fails": 0}
    if ok():
        if st.get("fails"):
            print(time.strftime("%H:%M:%S"), "web trả lời lại", flush=True)
        st["fails"] = 0
    else:
        st["fails"] = st.get("fails", 0) + 1
        busy = io_busy()
        print(time.strftime("%H:%M:%S"), f"web không trả lời ({st['fails']} lần liền), I/O {busy:.0f}%", flush=True)
        if st["fails"] >= FAILS_TO_RESTART and busy <= IO_BUSY:
            pid = web_pid()
            if pid:
                os.kill(pid, signal.SIGUSR1)      # ngăn xếp → journal của xuong-web
                time.sleep(2)
            subprocess.run(["systemctl", "--user", "restart", "xuong-web"])
            print(time.strftime("%H:%M:%S"), "đã restart xuong-web (ngăn xếp lúc treo: journalctl --user -u xuong-web)", flush=True)
            st = {"fails": 0, "last_restart": time.time()}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
