import { Config } from "@remotion/cli/config";

// P1.S3 — cấu hình probe. Concurrency để MẶC ĐỊNH ở đây; hai lần đo
// (mặc định vs --concurrency=12) truyền qua CLI để so được.
Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
