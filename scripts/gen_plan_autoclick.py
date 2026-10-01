"""Sinh plan-autoclick.md cho exp-create-video từ chính todos.md.

Lấy nguyên văn khối "📋 Prompt mở phiên — Pn" của từng phase, thay dòng
"Làm step: P<n>.S<n>" bằng step cụ thể, bỏ đoạn hướng dẫn chạy song song
(autoclick chạy tuần tự một cửa sổ), rồi thêm luật tick checkbox.
"""
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "todos.md"
TARGET = Path(__file__).resolve().parent.parent / "plan-autoclick.md"

# Step còn lại chạy được bằng máy, theo đúng thứ tự phụ thuộc.
STEPS = [
    # Lộ trình team (2026-10-01, research/10-team.md). Step cần tai/mắt/lựa chọn của
    # Tony hoặc cần video đã đăng nằm ở cuối file sinh ra, không ở đây.
    ("P3b.S4", 'Shot "bằng chứng": stat / chart / screenshot / code'),
    ("P3b.S5", "Caption theo cụm + nhấn từ khoá"),
    ("P4.S0", "Xương sống team: `state.json` + bộ chạy vai *(thêm 2026-10-01)*"),
    ("P4.S1", "T2: chất lượng hình ảnh bằng VLM"),
    ("P4.S2", "T3: sức hút nội dung"),
    ("P4.S3", "T4: độ chính xác sự thật (vai **fact-checker**)"),
    ("P4.S4", "Vòng lặp và ghi vết"),
    ("P5.S1", "Trend scout: topic hot hôm nay"),
    ("P5.S2", "Showrunner: series + lịch tuần"),
    ("P5.S3", "Brief → scriptwriter có nguồn"),
    ("P6.S1", "Caption/SEO writer: gói copy-dán"),
    ("P6.S2", "Bot Telegram (chuyển từ P5.S2)"),
    ("P6.S3", "Publisher TikTok (chuyển từ P5.S3)"),
    ("P6.S4", "Cron và nhịp chạy (chuyển từ P5.S4)"),
    ("P7.S1", "Analyst: thu số + báo cáo tuần"),
]

RUN_MODE = """CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây."""


def session_prompt(text: str, phase: str) -> str:
    """Lấy nội dung khối ``` trong mục '📋 Prompt mở phiên — Pn'."""
    m = re.search(
        rf"^### .*Prompt mở phiên — {phase}\s*$\n+^```\s*$\n(?P<body>.*?)^```\s*$",
        text, re.MULTILINE | re.DOTALL,
    )
    if not m:
        raise SystemExit(f"không tìm thấy khối prompt của {phase}")
    return m.group("body").rstrip("\n")


def build(prompt: str, phase: str, step: str, title: str) -> str:
    placeholder = rf"^Làm step: {re.escape(phase)}\.S<n>\..*$"
    replacement = (
        f'Làm step: {step}. Mở todos.md, tìm khối "### [ ] {step} — {title}" và làm đúng '
        f"theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó."
    )
    prompt, count = re.subn(placeholder, replacement, prompt, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"{step}: thay dòng 'Làm step' hụt (khớp {count} lần)")

    # Đoạn cuối nói cách chia worktree — vô nghĩa khi chạy tuần tự, và tệ hơn là
    # nó xui Claude đi tạo worktree giữa chừng.
    prompt = re.sub(r"\n*^(RÀNG BUỘC GPU|SONG SONG):.*\Z", "", prompt,
                    flags=re.MULTILINE | re.DOTALL)

    return "\n\n".join([
        prompt.rstrip("\n"),
        RUN_MODE,
        f'XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## {step}" và đổi checkbox trong\n'
        f'mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào\n'
        f'todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] {step}" trong todos.md\n'
        f"nữa thì tốt, để hai file khỏi lệch nhau.",
    ])


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    prompts = {p: session_prompt(text, p) for p in ("P3b", "P4", "P5", "P6", "P7")}

    out = [
        "# plan-autoclick.md — file cho tool autoclick đọc",
        "",
        "> **Đây KHÔNG phải roadmap.** Roadmap thật là [todos.md](todos.md); file này chỉ là",
        "> danh sách việc còn lại, viết theo đúng định dạng `tool-auto-click` parse được:",
        "> mỗi step một heading `##`, một checkbox, và một khối ``` không nhãn làm prompt.",
        ">",
        "> Prompt bên dưới **copy nguyên văn** từ các khối `📋 Prompt mở phiên` trong todos.md,",
        "> chỉ thay dòng `Làm step:` và bỏ phần hướng dẫn chạy song song. Sinh lại bằng",
        "> `scripts/gen_plan_autoclick.py` nếu todos.md đổi.",
        ">",
        "> **Tool đọc file NÀY để biết step nào xong**, nên checkbox ở đây mới là cái đếm.",
        "",
        "---",
        "",
    ]
    for step, title in STEPS:
        phase = step.split(".")[0]
        out += [
            f"## {step} — {title}",
            "",
            f"- [ ] {title}",
            "",
            "```",
            build(prompts[phase], phase, step, title),
            "```",
            "",
            "---",
            "",
        ]

    out += [
        "## Không đưa vào đây (tool không làm hộ được)",
        "",
        "Những việc còn lại trong todos.md cần Tony ra tay thật, không phải việc gõ code:",
        "",
        "- **P1.S1** — TikTok draft API: code xong, chờ phần bấm tay trong app.",
        "- **P3b.S2** — Giọng: Tony nghe mù X/Y/Z ở out/p3b-nghe-mu/ rồi chọn cách ghép.",
        "- **P3b.S3** — Phát âm thuật ngữ: Tony duyệt từng mục từ điển respelling.",
        "- **P3b.S6** — Nhạc nền: Tony chọn ACE-Step / thư viện CC0 / để trống.",
        "- **P3b.S8** — Model ảnh: so mù với SDXL, Tony chấm.",
        "- **P3b.S10** — Parallax: Tony so p3b-d với p3b-b (phần zoom-punch làm sau khi Tony chọn).",
        "- **P7.S2** — Thử format/độ dài: cần video đã đăng + số thật.",
        "- **P7.S3** — Xem lại QC + các vai sau 20 video: phải có 20 video thật đã.",
        "",
        "Mục **Nợ kỹ thuật đã biết** ở cuối todos.md cũng để nguyên đó — phần lớn là câu hỏi",
        "chưa quyết, không phải việc giao được.",
        "",
    ]
    TARGET.write_text("\n".join(out), encoding="utf-8")
    print(f"✓ {TARGET} — {len(STEPS)} step")


main()
