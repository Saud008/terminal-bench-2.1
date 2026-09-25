"""Sheet compositor and bilinear sample sampler."""

from __future__ import annotations

from PIL import Image


def blit_content_only(
    sheet: Image.Image,
    sheet_x: int,
    sheet_y: int,
    pad: int,
    content_w: int,
    content_h: int,
    src: Image.Image,
) -> None:
    px = src.load()
    apx = sheet.load()
    for y in range(content_h):
        for x in range(content_w):
            tx = sheet_x + pad + x
            ty = sheet_y + pad + y
            if 0 <= tx < sheet.width and 0 <= ty < sheet.height:
                apx[tx, ty] = px[x, y]


def compose_sheet(
    layout: list[dict],
    sheet_w: int,
    sheet_h: int,
    pad: int,
) -> Image.Image:
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for item in layout:
        blit_content_only(
            sheet,
            item["sheet_x"],
            item["sheet_y"],
            pad,
            item["content_w"],
            item["content_h"],
            item["image"],
        )
    return sheet


def sample_bilinear(
    rgba: bytes,
    sheet_w: int,
    sheet_h: int,
    u0: float,
    v0: float,
    u1: float,
    v1: float,
    u: float,
    v: float,
) -> list[int]:
    px = u0 + u * (u1 - u0)
    py = v0 + v * (v1 - v0)
    fx = px * sheet_w - 0.5
    fy = py * sheet_h - 0.5
    x0 = max(int(fx // 1), 0)
    y0 = max(int(fy // 1), 0)
    x1 = min(x0 + 1, sheet_w - 1)
    y1 = min(y0 + 1, sheet_h - 1)
    tx = fx - x0
    ty = fy - y0

    def pix(x: int, y: int) -> list[int]:
        idx = (y * sheet_w + x) * 4
        return list(rgba[idx : idx + 4])

    c00 = pix(x0, y0)
    c10 = pix(x1, y0)
    c01 = pix(x0, y1)
    c11 = pix(x1, y1)
    out = []
    for i in range(4):
        top = c00[i] + (c10[i] - c00[i]) * tx
        bot = c01[i] + (c11[i] - c01[i]) * tx
        out.append(round(top + (bot - top) * ty))
    return out
