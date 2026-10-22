# Kakuro assets (tách từ Kakuro_Tutorial.pdf)

PDF gốc **không có ảnh raster** – mọi thứ là vector/font, nên asset xuất ra là SVG (phóng to không vỡ, đổi màu được).

## Cấu trúc
- `svg/cells/`  cell-empty, cell-highlight, cell-void, tri-up/down/left/right (tam giác gợi ý "dual triangular"), ring (vòng tròn đánh dấu), border-edge
- `svg/digits-hand/` hand-1..9: chữ số người chơi điền (nét viết tay, đã outline từ PDF)
- `svg/digits-clue/` clue-0..9: chữ số gợi ý (Helvetica Bold đã outline) – ghép lại thành số nhiều chữ số
- `svg/labels/` lbl-A..F, lbl-1..6: nhãn hàng/cột (Helvetica Oblique)
- `svg/sprite.svg`: toàn bộ ở trên dạng `<symbol>` (dùng với `<use href="#hand-5">`; đổi màu chữ số bằng CSS `color`)
- `css/theme.css`: biến màu `--kk-*` + 4 theme (classic = màu đo từ PDF, midnight, mint, sunset)
- `tokens.json`: kích thước (1 ô = 48, tam giác sâu 24, viền 1, lưới 0.5) và màu gốc
- `fonts/`: font nhúng trong PDF (xem lưu ý), `preview.html`: bàn chơi mẫu + thư viện (mở trực tiếp bằng trình duyệt)

## Màu gốc đo từ PDF
ô #FFF · ô tô #E6E6E6 · lưới #7F7F7F 0.5pt · nền gợi ý #EEE · viền gợi ý #777 1pt · số gợi ý #444 · số điền #777 · nhãn #505028 · vòng tròn #000

## Cách đổi style
- File SVG riêng dùng `var(--kk-xxx, màu_gốc)`: chỉ đổi được khi **inline** SVG. Nếu nạp bằng `<img>` thì chỉ thấy màu gốc.
- Khuyên dùng `sprite.svg` + `<use>`: đổi `color`/biến CSS là đổi toàn bộ.

## Lưu ý font
Font trong PDF chỉ là **subset** (chỉ chứa ký tự đã dùng, không có đủ chữ/số) và là font thương mại (Iowan Old Style của Apple, Anime Ace, Franklin Gothic, Helvetica/Arial) – không nên phát hành game kèm chúng. Số trong ô đã được xuất sang SVG nên game không cần font. Font thay thế miễn phí gợi ý: tiêu đề → Crimson Pro / Source Serif 4; số gợi ý → Inter / Roboto Bold; chữ viết tay → Patrick Hand / Comic Neue.
Các số gợi ý nhiều chữ số (vd 16, 24, 45) không xuất sẵn – ghép từ clue-0..9 (xem hàm `glyphs()` trong preview.html).
