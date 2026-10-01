import { Config } from "@remotion/cli/config";

// P1.S3 — cấu hình probe. Concurrency để MẶC ĐỊNH ở đây; hai lần đo
// (mặc định vs --concurrency=12) truyền qua CLI để so được.
Config.setVideoImageFormat("jpeg");
// P3b.S1 (2026-10-01): JPEG mặc định ~80 làm viền chữ dính artifact TRƯỚC cả khi
// TikTok nén lại lần nữa. 95 + CRF 18 là đủ sạch mà file không phình quá.
Config.setJpegQuality(95);
Config.setCodec("h264");
Config.setCrf(18);
Config.setPixelFormat("yuv420p");
// P3b.S10 (2026-10-01): parallax 2.5D vẽ bằng WebGL. Chrome headless không bật
// WebGL ổn định nếu không chỉ định. `swangle` = SwiftShader (CPU): chậm hơn `angle`
// nhưng KHÔNG chạm GPU — 2060 dùng chung với dự án khác, và render CPU-bound vốn
// là lý do chọn Remotion. Nếu chậm quá ngưỡng P3b.S10 thì thử "angle".
Config.setChromiumOpenGlRenderer("swangle");
