## remotion-dev/remotion · audited 2026-08-04

Purpose we'd use it for: khối dựng video — đọc `video-spec.json`, xuất mp4 1080×1920.
License: **NOASSERTION** (custom, hai tầng) | weights: n/a   Archived: n   Fork of: n/a

### Signals [gh api, 2026-08-04]

```
last commit:    2026-08-03 (0d ago)        commits/90d: 100 (chạm trần trang, thực tế ≥100)
absence factor: 1                          ← rủi ro chính
latest release: v4.0.505 on 2026-08-03     release vs last commit: 0 ngày
1st response:   median 0d, 4/30 issue gần đây được trả lời
PR closure:     9 open vs 6.359 closed/merged all-time
scorecard:      không quét (dưới ngưỡng phổ biến của OpenSSF)
stars:          55.438
```

### Gates

| Gate | Kết quả | Ghi chú |
|---|---|---|
| license | ⚠️ **pass có điều kiện** | free cho cá nhân và tổ chức ≤3 người; DTG lớn hơn thì phải mua |
| alive | ✅ pass | commit hôm qua, release cùng ngày |
| bus factor | ⚠️ **absence factor = 1** | nhưng repo commit hằng ngày → theo tiêu chí CHAOSS chỉ là *rủi ro ghi nhận*, không phải fail (fail cần cả absence=1 **và** 6 tháng không commit) |
| runs | ✅ **verified** | render 60s 1080×1920 chạy được trên tony — xem `research/probes/p1s3-remotion.md` |
| legible | ✅ pass | docs đầy đủ ở remotion.dev, 6.359 PR đã merge |

### License — nguyên văn, đây là thứ phải ghi chính xác

Nguồn: `https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md`
đọc **2026-08-04**, copyright ghi © 2026.

**Ai được dùng miễn phí** (nguyên văn mục "Eligibility"):

> You are eligible to use Remotion for free if you are:
> - an individual
> - a for-profit organization with up to 3 employees
> - a non-profit or not-for-profit organization
> - evaluating whether Remotion is a good fit, and are not yet using it in a commercial way

**Được làm gì khi miễn phí** (nguyên văn):

> Permission is hereby granted, free of charge, to any person eligible for the "Free
> License", to use the software non-commercially or **commercially** for the purpose of
> creating videos and images and to modify the software to their own liking […]

→ Nghĩa là: **cá nhân được dùng thương mại miễn phí.** Ngưỡng 3 người áp cho
*for-profit organization*, không áp cho cá nhân.

**Cấm** (nguyên văn):

> It is not allowed to copy or modify Remotion code for the purpose of selling, renting,
> licensing, relicensing, or sublicensing your own derivate of Remotion.

→ Dự án này **không** chạm điều cấm: ta dùng Remotion để dựng video, không bán lại Remotion.

**Giá Company License** [remotion.pro/license, 2026-08-04, *reported* — đọc qua trang giá,
chưa qua bộ phận sales]:

| Gói | Giá | Cho ai |
|---|---|---|
| Free | 0đ | cá nhân, tổ chức ≤3 người |
| Remotion for Creators | $25/tháng/ghế, tối thiểu $75/tháng (3 ghế) | tạo video số lượng ít bằng code |
| Remotion for Automators | $0,01/lần render, tối thiểu $100/tháng | app/hệ thống sinh video tự động |
| Enterprise | từ $500/tháng | nhu cầu nâng cao |

⚠️ Lưu ý gói **Automators** — hệ này *là* một hệ sinh video tự động. Nếu DTG dùng
thương mại thì đây mới là gói đúng, không phải Creators.

**Remotion 5.0 sẽ đổi license** [PR #3750, đọc 2026-08-04, *reported*]:
LICENSE.md hiện tại mở đầu bằng dòng "In Remotion 5.0, the license will slightly change."
Thay đổi đã xác định được: **contractor cũng tính vào team size** — trước đây một công ty
chỉ thuê contractor thì không bao giờ phải mua license. PR chưa merge tại thời điểm đọc.
→ **Phải kiểm lại license trước khi nâng lên 5.x.** Đừng nâng major version tự động.

### Tình trạng hiện tại của Tony

Tony dùng **cá nhân** → thuộc diện Free License, **kể cả khi kiếm tiền từ video**.
Điều kiện này chỉ đổi khi DTG (>3 người) dùng nó cho việc thương mại.
Đây là **câu hỏi pháp lý cho Tony, không phải câu hỏi kỹ thuật** — card này chỉ ghi
điều kiện, không kết luận thay.

### What the issue tracker says

- Trả lời nhanh nhưng **thưa**: chỉ 4/30 issue gần đây có phản hồi (median 0 ngày khi có).
  Đọc theo `references/signals.md`: repo lớn thường lọc issue mạnh, nhưng tỉ lệ 13% là thấp.
- 9 PR mở trên 6.359 đã đóng → không có tồn đọng. Kỷ luật release rất tốt (release cùng
  ngày với commit cuối).

### Integration cost

Đã trả xong phần lớn: `npm install` 17s / 250 package; render chạy ngay không phải vá gì.
Ràng buộc thêm: cần Node runtime (v25.8.2 đã có) và Chrome Headless Shell (~150MB, Remotion
tự tải lần đầu). **0 VRAM** — verified qua P1.S3, đúng như lý do đã chọn nó.

### Exit plan

Ranh giới `video-spec.json` là thứ làm exit plan này rẻ: Python sinh spec, không gọi thẳng
Remotion. Nếu Remotion chết hoặc license thành vấn đề → **Revideo** (MIT, cùng mô hình
TypeScript/React), viết lại lớp component, không đụng phần Python. Ước lượng: 2–4 ngày.

**Verdict: adopt** — khoẻ nhất trong bốn repo, và ranh giới kiến trúc đã dựng sẵn đường thoát.
**Confidence: verified** (license đọc nguyên văn; render tự đo; giá là *reported*).
