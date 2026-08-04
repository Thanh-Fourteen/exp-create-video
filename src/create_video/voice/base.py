"""Interface cho mọi backend TTS.

Lý do tồn tại: Tony đang tự phát triển model TTS. VieNeu là bản tạm để thông
pipeline. Khi model của Tony xong thì **đổi một dòng trong `configs/models.yaml`**,
không sửa code pipeline. Đó là toàn bộ mục đích của file này.

Ràng buộc cứng: **timestamp từng từ là bắt buộc**. Phụ đề karaoke của Remotion ăn
thẳng từ `TTSResult.words`; không có timestamp thì không có phụ đề động, mà phụ đề
động là một trong ba thứ tạo nên "video hay" ở đây (xem `research/05-decision.md`).
Backend nào không tự trả timestamp thì phải align thêm — không được trả về rỗng.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Word:
    """Một từ kèm mốc thời gian trong wav, đơn vị **giây**."""

    w: str
    start: float
    end: float

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"end < start ở từ {self.w!r}: {self.start} → {self.end}")

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class TTSResult:
    """Kết quả một lần tổng hợp.

    `words` phải phủ đúng thứ tự đọc và **không được rỗng** — QC tầng 1 kiểm
    `require_word_level` và `max_drift_ms` dựa vào đây (`configs/thresholds.yaml`).
    """

    wav_path: Path
    sample_rate: int
    duration_sec: float
    words: list[Word] = field(default_factory=list)
    # Backend nào sinh ra, và timestamp đến từ đâu — cần khi truy lỗi phụ đề lệch.
    backend: str = ""
    timestamp_source: str = ""  # "native" | "forced_aligner" | "even_split"

    def validate(self) -> None:
        """Fail sớm, thông báo rõ. Gọi trước khi đưa xuống bước dựng."""
        if not self.wav_path.exists():
            raise FileNotFoundError(f"Không thấy wav: {self.wav_path}")
        if not self.words:
            raise ValueError(
                "words rỗng — phụ đề karaoke không dựng được. "
                "Xem phương án dự phòng ở research/probes/p1s2-tts.md."
            )
        for a, b in zip(self.words, self.words[1:]):
            if b.start < a.start:
                raise ValueError(f"words không đúng thứ tự: {a.w!r} rồi {b.w!r}")
        last = self.words[-1].end
        # Cho phép lệch nhỏ ở đuôi; lệch lớn nghĩa là align hỏng.
        if last > self.duration_sec + 0.5:
            raise ValueError(
                f"timestamp vượt quá độ dài wav: {last:.2f}s > {self.duration_sec:.2f}s"
            )

    def shift(self, offset_sec: float) -> "TTSResult":
        """Dời mọi timestamp thêm `offset_sec`.

        Dùng khi ghép nhiều đoạn wav thành một (P3.S2). **Đây là chỗ dễ sai nhất
        của cả khối voice**: quên cộng offset thì phụ đề lệch dần về cuối video,
        và lỗi đó không nhìn ra khi test đoạn ngắn.
        """
        return TTSResult(
            wav_path=self.wav_path,
            sample_rate=self.sample_rate,
            duration_sec=self.duration_sec,
            words=[Word(w.w, w.start + offset_sec, w.end + offset_sec) for w in self.words],
            backend=self.backend,
            timestamp_source=self.timestamp_source,
        )


class TTSBackend(ABC):
    """Mọi backend TTS phải cài đủ ba thứ dưới đây."""

    name: str = "base"

    @abstractmethod
    def synth(self, text: str, speaker: str | None = None) -> TTSResult:
        """Tổng hợp `text` tiếng Việt, trả wav + timestamp từng từ."""

    @abstractmethod
    def health(self) -> bool:
        """Backend đã sẵn sàng chưa. Pipeline gọi trước khi vào job dài."""

    def close(self) -> None:
        """Nhả tài nguyên.

        Backend nào nạp model lên GPU **phải** override và gọi
        `torch.cuda.empty_cache()`. 6GB của tony không cho giữ hai model cùng lúc —
        quên chỗ này thì OOM xuất hiện ở bước sau, trông như lỗi ngẫu nhiên.
        """
        return None
