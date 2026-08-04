---
name: route
description: Phân tích một yêu cầu và chọn skill phù hợp — giải thích chọn cái nào, theo thứ tự nào, thiếu thông tin gì, rồi chạy bước đầu tiên. Dùng khi không rõ nên bắt đầu từ đâu, hoặc muốn thấy kế hoạch trước khi chạy.
argument-hint: [yêu cầu cần phân tích]
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Glob, Grep
---

# Định tuyến: $ARGUMENTS

`disable-model-invocation: true` là cố ý — router mà model tự gọi được thì thừa: gọi được router nghĩa là gọi thẳng skill đích cũng được. Skill này chỉ chạy khi **bạn** gõ `/route`, để thấy kế hoạch trước khi làm.

Nếu `$ARGUMENTS` rỗng: lấy yêu cầu gần nhất của người dùng trong hội thoại làm đầu vào.

## Phân tích

Trả lời 4 câu, ngắn gọn:

1. **Người dùng thực sự muốn gì?** Một câu. Phân biệt yêu cầu bề mặt với mục tiêu thật — "tìm paper về OCR" thường có mục tiêu thật là "chọn được hướng làm".
2. **Đang ở đâu trong chuỗi?** Kiểm tra `research/` xem file nào đã tồn tại:
   - chưa có gì → đầu chuỗi
   - có `00-problem.md`, chưa có `05-decision.md` → giữa Phase 2–3
   - có `05-decision.md` còn `provisional` → thiếu dữ liệu thật, chưa dựng repo được
   - `05-decision.md` đã chốt → sẵn sàng `create-repo`
3. **Thiếu thông tin gì để chạy được?** Liệt kê cái chặn, không liệt kê cái "biết thì tốt".
4. **Skill nào, thứ tự nào?** Theo bảng và quy tắc phân biệt trong `.claude/rules/skill-routing.md`.

Nếu kế hoạch định tuyến sang một domain pack (`<chủ đề>-landscape`), **đọc dòng
`last swept` của pack đó và báo ra**. Pack là snapshot, không phải kiến thức
sống. Ngưỡng ở `research-topic/references/domain-pack.md`: ≤4 tuần thì thay được
Phase 1–2; >12 tuần thì chỉ còn taxonomy dùng được, mọi tên model và điểm số
trong đó coi như chưa verify. Định tuyến vào một pack cũ mà không nói gì chính
là cách sự cố 2026-07-27 xảy ra.

## Đầu ra

```
Mục tiêu thật:  <một câu>
Vị trí:         <bước nào trong chuỗi, dựa trên file nào trong research/>
Chặn ở:         <thông tin còn thiếu, hoặc "không">

Kế hoạch:
  1. /<skill> <args>   — <vì sao>
  2. /<skill> <args>   — <vì sao>   [chỉ khi bước 1 xong]

Không dùng: /<skill> — <vì sao loại>
Độ tươi:    <pack + ngày last swept, hoặc "không dùng pack">
```

Phần "Không dùng" bắt buộc có ít nhất một dòng. Nói rõ vì sao loại một skill có ích ngang việc chọn đúng skill.

## Sau khi phân tích

Chạy **bước 1**. Không chạy bước 2 — chuỗi do người dùng quyết định nhịp.

Nếu bước 1 bị chặn vì thiếu thông tin: hỏi đúng những câu ở mục "Chặn ở", không hỏi thêm.

## Quy tắc

- Chọn skill **hẹp nhất khớp được**. Câu hỏi OCR nhanh → `ocr-landscape`, không phải `research-topic`.
- Skill đã nạp trong phiên này thì không nạp lại — nội dung còn trong context.
- Không có skill nào khớp → nói thẳng và trả lời trực tiếp. Ép một skill vào việc không hợp còn tệ hơn không dùng skill.
