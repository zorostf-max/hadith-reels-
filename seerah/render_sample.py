#!/usr/bin/env python3
"""Sample scene renderer: still illustration + slow camera move + speech bubbles.
Usage: render.py <image> <audio.wav> <out.mp4> [--frame T out.png]
"""
import sys, math, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "Baloo.ttf")


def font(size, weight=700):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---- timeline (seconds) -------------------------------------------------
DUR = 15.2
# camera keyframes: (time, zoom, centre-x fraction, centre-y fraction)
CAM = [(0.0, 1.22, 0.34, 0.52), (3.9, 1.27, 0.34, 0.53),
       (5.4, 1.20, 0.64, 0.47), (11.3, 1.25, 0.66, 0.47),
       (12.6, 1.00, 0.50, 0.50), (15.2, 1.04, 0.50, 0.50)]

BUBBLES = [
    # start, end, lines, box centre (x,y), tail tip (x,y), fill, text colour
    dict(t0=0.45, t1=3.95, lines=["يا أبي، لماذا سُمّي", "عامُ الفيل بهذا الاسم؟"],
         c=(520, 600), tip=(520, 850), fill=(255, 244, 248), fg=(92, 36, 66), size=60),
    dict(t0=4.3, t1=11.25, lines=["حكايةُ جيشٍ جاء", "ليهدم الكعبة…"],
         c=(590, 520), tip=(770, 740), fill=(255, 250, 235), fg=(52, 40, 20), size=64),
    dict(t0=11.6, t1=14.9, lines=["اجلسوا يا أولادي،", "أحكي لكم"],
         c=(540, 600), tip=(760, 760), fill=(255, 250, 235), fg=(52, 40, 20), size=64),
]
TITLE = dict(t0=12.2, text="السيرة النبوية · الحلقة ١", sub="عام الفيل")


def cam_at(t):
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in zip(CAM, CAM[1:]):
        if t <= t1:
            k = smooth((t - t0) / (t1 - t0))
            return (z0 + (z1 - z0) * k, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
    return CAM[-1][1:]


def draw_bubble(layer, b, k):
    """k = 0..1 pop-in progress."""
    f = font(b["size"])
    d = ImageDraw.Draw(layer)
    widths = [d.textlength(s, font=f, direction="rtl", language="ar") for s in b["lines"]]
    lh = int(b["size"] * 1.45)
    bw = int(max(widths) + 110)
    bh = int(lh * len(b["lines"]) + 70)
    cx, cy = b["c"]
    s = 0.6 + 0.4 * ease(k)
    alpha = int(255 * ease(k * 1.6))
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    x0, y0, x1, y1 = cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((x0 + 6, y0 + 14, x1 + 6, y1 + 14), radius=58, fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    tile.alpha_composite(sh)
    # tail
    tx, ty = b["tip"]
    base = max(x0 + 80, min(x1 - 80, tx))
    td.polygon([(base - 38, y1 - 6), (base + 38, y1 - 6),
                (base + (tx - base) * 0.35, y1 + min(90, (ty - y1) * 0.5))], fill=b["fill"])
    td.rounded_rectangle((x0, y0, x1, y1), radius=58, fill=b["fill"])
    ty0 = cy - (lh * len(b["lines"])) // 2
    for i, line in enumerate(b["lines"]):
        td.text((cx, ty0 + i * lh + lh // 2), line, font=f, fill=b["fg"],
                anchor="mm", direction="rtl", language="ar")
    if s < 0.999:
        bb = (max(0, x0 - 40), max(0, y0 - 40), min(W, x1 + 60), min(H, y1 + 130))
        crop = tile.crop(bb)
        nw, nh = max(1, int(crop.width * s)), max(1, int(crop.height * s))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tile.paste(crop, (bb[0] + (bb[2] - bb[0] - nw) // 2, bb[1] + (bb[3] - bb[1] - nh)))
    if alpha < 255:
        a = tile.getchannel("A").point(lambda v: v * alpha // 255)
        tile.putalpha(a)
    layer.alpha_composite(tile)


def draw_title(layer, k):
    d = ImageDraw.Draw(layer)
    f1, f2 = font(46, 600), font(84, 800)
    a = int(255 * ease(k))
    dy = int(30 * (1 - ease(k)))
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    w2 = td.textlength(TITLE["sub"], font=f2, direction="rtl", language="ar")
    w1 = td.textlength(TITLE["text"], font=f1, direction="rtl", language="ar")
    bw = int(max(w1, w2) + 120)
    x0, y0 = (W - bw) // 2, 205 - dy
    td.rounded_rectangle((x0, y0, x0 + bw, y0 + 230), radius=44, fill=(16, 28, 54, 215),
                         outline=(232, 190, 96, 255), width=4)
    td.text((W // 2, y0 + 62), TITLE["text"], font=f1, fill=(240, 214, 150), anchor="mm",
            direction="rtl", language="ar")
    td.text((W // 2, y0 + 150), TITLE["sub"], font=f2, fill=(255, 250, 240), anchor="mm",
            direction="rtl", language="ar")
    if a < 255:
        tile.putalpha(tile.getchannel("A").point(lambda v: v * a // 255))
    layer.alpha_composite(tile)


def frame(src, t):
    z, cxf, cyf = cam_at(t)
    sw, sh = src.size
    # base crop that fills 9:16
    if sw / sh > W / H:
        ch = sh; cw = sh * W / H
    else:
        cw = sw; ch = sw * H / W
    cw /= z; ch /= z
    cx = min(max(cxf * sw, cw / 2), sw - cw / 2)
    cy = min(max(cyf * sh, ch / 2), sh - ch / 2)
    img = src.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    layer = img.convert("RGBA")
    # soft lantern flicker (whole-frame warmth, very subtle)
    fl = 0.5 + 0.5 * math.sin(t * 5.1) * math.sin(t * 1.7 + 1.0)
    warm = Image.new("RGBA", (W, H), (255, 170, 60, int(10 * fl)))
    layer.alpha_composite(warm)
    for b in BUBBLES:
        if b["t0"] <= t <= b["t1"]:
            kin = (t - b["t0"]) / 0.28
            kout = (b["t1"] - t) / 0.2
            draw_bubble(layer, b, min(kin, kout, 1.0))
    if t >= TITLE["t0"]:
        draw_title(layer, (t - TITLE["t0"]) / 0.5)
    # fade in / out
    f = min(t / 0.4, (DUR - t) / 0.5, 1.0)
    out = layer.convert("RGB")
    if f < 1:
        out = Image.blend(Image.new("RGB", (W, H), (8, 12, 26)), out, max(0.0, f))
    return out


def main():
    src = Image.open(sys.argv[1]).convert("RGB")
    if "--frame" in sys.argv:
        i = sys.argv.index("--frame")
        frame(src, float(sys.argv[i + 1])).save(sys.argv[i + 2])
        return
    audio, out = sys.argv[2], sys.argv[3]
    tmp = out + ".part.mp4"
    p = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
         "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp],
        stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(frame(src, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
        print("ok", out)
    else:
        sys.exit("ffmpeg failed")


if __name__ == "__main__":
    main()
