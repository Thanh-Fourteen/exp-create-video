/**
 * Chuỗi font cho headless Chrome.
 *
 * Google Fonts phát Be Vietnam Pro thành **một file TTF cho mỗi weight**, và
 * fontconfig đăng ký chúng thành các family RIÊNG ("Be Vietnam Pro ExtraBold",
 * "Be Vietnam Pro Black") chứ không gộp vào một family theo weight. Xin đúng
 * "Be Vietnam Pro" ở weight 800 thì Chrome không tìm thấy và rơi về font hệ
 * thống — chữ vẫn hiện, vẫn đủ dấu, nên **lỗi này không tự lộ ra**: chỉ khi so
 * hai frame cạnh nhau mới thấy sai font.
 *
 * Vì thế liệt kê cả tên biến thể. Font cài ở `~/.fonts/be-vietnam-pro/`.
 */
export const fontStack = (family: string): string =>
  [
    `"${family}"`,
    `"${family} ExtraBold"`,
    `"${family} Black"`,
    '"Noto Sans"',
    "system-ui",
    "sans-serif",
  ].join(", ");
