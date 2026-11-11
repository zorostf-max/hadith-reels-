#!/usr/bin/env python3
"""Render a seerah episode: still illustrations + slow camera moves + speech bubbles /
captions + voice clips.  Usage:
  render_episode.py seerah/ep01            -> seerah/ep01/episode.mp4
  render_episode.py seerah/ep01 --check    -> one still per scene in seerah/ep01/check/
Audio clips are expected at <ep>/audio/sNN[a-d].mp3 in script order; images at
<ep>/img/<name>.png (or the path given in script.json "images.<name>.file").
"""
import sys, os, json, math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "assets", "Baloo.ttf")
LEAD, GAP, TAIL, XF = 0.45, 0.45, 0.7, 0.45   # seconds
_fonts = {}


def font(size, weight=700):
    k = (size, weight)
    if k not in _fonts:
        f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _fonts[k] = f
    return _fonts[k]


def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())


# speaker anchors on the majlis picture, in screen coords at zoom 1 (head tops)
HEADS = {"omar": (150, 960), "maryam": (390, 1010), "father": (800, 840)}
STYLE = {"father": dict(fill=(255, 250, 235), fg=(52, 40, 20), size=62),
         "maryam": dict(fill=(255, 240, 246), fg=(96, 34, 66), size=60),
         "omar": dict(fill=(236, 246, 255), fg=(24, 52, 92), size=60)}
BUBBLE_C = {"father": (640, 560), "maryam": (470, 640), "omar": (440, 600)}

# camera paths: list of (u, zoom, cx, cy) with u in 0..1 of scene time
CAMS = {
    "children": [(0, 1.04, .5, .5), (1, 1.09, .45, .52)],
    "children_then_father": [(0, 1.04, .47, .51), (1, 1.08, .53, .5)],
    "wide": [(0, 1.08, .5, .5), (1, 1.0, .5, .5)],
    "slow_push": [(0, 1.0, .5, .5), (1, 1.14, .5, .48)],
    "slow_pull": [(0, 1.14, .5, .5), (1, 1.0, .5, .5)],
    "pan_right": [(0, 1.18, .40, .52), (1, 1.18, .60, .5)],
    "tilt_down": [(0, 1.16, .5, .40), (1, 1.10, .5, .58)],
}


def cam_at(path, u):
    for (u0, z0, x0, y0), (u1, z1, x1, y1) in zip(path, path[1:]):
        if u <= u1:
            k = smooth((u - u0) / (u1 - u0))
            return z0 + (z1 - z0) * k, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    return path[-1][1:]


PANEL_H, PANEL_CY = 1080, 870   # landscape pictures: framed band over a blurred copy
_bg = {}


def shot(src, z, cxf, cyf):
    sw, sh = src.size
    if sw > sh:
        if id(src) not in _bg:
            bh = H; bw = int(sw * H / sh)
            b = src.resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, 0, (bw - W) // 2 + W, H))
            b = b.filter(ImageFilter.GaussianBlur(28))
            b = Image.blend(Image.new("RGB", (W, H), (8, 12, 26)), b, 0.55)
            _bg[id(src)] = b
        out = _bg[id(src)].copy()
        ph = PANEL_H
        cw = sh * W / ph / z; ch = sh / z
        cx = min(max(cxf * sw, cw / 2), sw - cw / 2)
        cy = min(max(cyf * sh, ch / 2), sh - ch / 2)
        panel = src.resize((W, ph), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        y0 = PANEL_CY - ph // 2
        out.paste(panel, (0, y0))
        d = ImageDraw.Draw(out)
        d.line((0, y0 - 2, W, y0 - 2), fill=(232, 190, 96), width=4)
        d.line((0, y0 + ph + 1, W, y0 + ph + 1), fill=(232, 190, 96), width=4)
        return out
    if sw / sh > W / H:
        ch = sh; cw = sh * W / H
    else:
        cw = sw; ch = sw * H / W
    cw /= z; ch /= z
    cx = min(max(cxf * sw, cw / 2), sw - cw / 2)
    cy = min(max(cyf * sh, ch / 2), sh - ch / 2)
    return src.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))


def fade_alpha(tile, a):
    if a < 255:
        tile.putalpha(tile.getchannel("A").point(lambda v: v * a // 255))
    return tile


def draw_bubble(layer, who, lines, k):
    st = STYLE[who]; f = font(st["size"])
    d = ImageDraw.Draw(layer)
    widths = [d.textlength(s, font=f, direction="rtl", language="ar") for s in lines]
    lh = int(st["size"] * 1.45)
    bw = int(min(W - 60, max(widths) + 110)); bh = int(lh * len(lines) + 70)
    cx, cy = BUBBLE_C[who]
    cx = min(max(cx, bw // 2 + 30), W - bw // 2 - 30)
    tx, ty = HEADS[who]
    x0, y0, x1, y1 = cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 6, y0 + 14, x1 + 6, y1 + 14), radius=58, fill=(0, 0, 0, 110))
    tile.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    td = ImageDraw.Draw(tile)
    base = max(x0 + 90, min(x1 - 90, tx))
    tip_y = min(ty - 40, y1 + 150)
    td.polygon([(base - 40, y1 - 8), (base + 40, y1 - 8), (base + (tx - base) * 0.6, tip_y)], fill=st["fill"])
    td.rounded_rectangle((x0, y0, x1, y1), radius=58, fill=st["fill"])
    ty0 = cy - (lh * len(lines)) // 2
    for i, line in enumerate(lines):
        td.text((cx, ty0 + i * lh + lh // 2), line, font=f, fill=st["fg"], anchor="mm", direction="rtl", language="ar")
    s = 0.6 + 0.4 * ease(k)
    if s < 0.999:
        bb = (max(0, x0 - 40), max(0, y0 - 40), min(W, x1 + 60), min(H, int(tip_y) + 40))
        crop = tile.crop(bb)
        nw, nh = max(1, int(crop.width * s)), max(1, int(crop.height * s))
        tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tile.paste(crop.resize((nw, nh), Image.BILINEAR), (bb[0] + (bb[2] - bb[0] - nw) // 2, bb[1] + (bb[3] - bb[1] - nh)))
    layer.alpha_composite(fade_alpha(tile, int(255 * ease(k * 1.6))))


def wrap(text, f, maxw, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f, direction="rtl", language="ar") <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def draw_caption(layer, text, k):
    f = font(58, 700)
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    lines = wrap(text, f, W - 200, td)
    lh = 84; bh = lh * len(lines) + 60
    y1 = H - 250; y0 = y1 - bh
    dy = int(24 * (1 - ease(k)))
    td.rounded_rectangle((70, y0 + dy, W - 70, y1 + dy), radius=40, fill=(14, 24, 48, 205),
                         outline=(232, 190, 96, 255), width=3)
    for i, s in enumerate(lines):
        td.text((W // 2, y0 + dy + 30 + i * lh + lh // 2), s, font=f, fill=(255, 246, 225), anchor="mm",
                direction="rtl", language="ar")
    layer.alpha_composite(fade_alpha(tile, int(255 * ease(k))))


def draw_card(layer, top, main, k, y=205):
    f1, f2 = font(46, 600), font(84, 800)
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    w = max(td.textlength(top, font=f1, direction="rtl", language="ar"),
            td.textlength(main, font=f2, direction="rtl", language="ar"))
    bw = int(w + 120); x0 = (W - bw) // 2; y0 = y - int(30 * (1 - ease(k)))
    td.rounded_rectangle((x0, y0, x0 + bw, y0 + 230), radius=44, fill=(16, 28, 54, 215),
                         outline=(232, 190, 96, 255), width=4)
    td.text((W // 2, y0 + 62), top, font=f1, fill=(240, 214, 150), anchor="mm", direction="rtl", language="ar")
    td.text((W // 2, y0 + 150), main, font=f2, fill=(255, 250, 240), anchor="mm", direction="rtl", language="ar")
    layer.alpha_composite(fade_alpha(tile, int(255 * ease(k))))


def draw_label(layer, text):
    f = font(36, 600); d = ImageDraw.Draw(layer)
    d.text((W // 2, 95), text, font=f, fill=(255, 240, 205, 210), anchor="mm", direction="rtl", language="ar",
           stroke_width=3, stroke_fill=(10, 16, 32, 160))


class Episode:
    def __init__(self, ep):
        self.ep = ep
        self.s = json.load(open(os.path.join(ep, "script.json")))
        self.imgs = {}
        for name, spec in self.s["images"].items():
            p = os.path.join(ep, spec["file"]) if "file" in spec else os.path.join(ep, "img", name + ".png")
            self.imgs[name] = Image.open(p).convert("RGB")
        # timeline
        self.scenes, self.clips, t = [], [], 0.0
        for sc in self.s["scenes"]:
            lines, lt = [], LEAD
            multi = len(sc["lines"]) > 1
            for i, ln in enumerate(sc["lines"]):
                a = os.path.join(ep, "audio", "s%02d%s.mp3" % (sc["id"], "abcd"[i] if multi else ""))
                d = dur(a)
                lines.append(dict(ln, t0=lt, t1=lt + d))
                self.clips.append((t + lt, a))
                lt += d + GAP
            extra = 1.8 if sc.get("title_card") else 0
            extra += 2.2 if sc.get("end_card") else 0
            length = lt - GAP + TAIL + extra
            self.scenes.append(dict(sc, start=t, length=length, lines=lines))
            t += length
        self.total = t

    def scene_frame(self, sc, lt):
        u = lt / sc["length"]
        z, cx, cy = cam_at(CAMS.get(sc.get("cam"), CAMS["slow_push"]), u)
        layer = shot(self.imgs[sc["image"]], z, cx, cy).convert("RGBA")
        if sc["image"] == "majlis":
            fl = 0.5 + 0.5 * math.sin(lt * 5.1) * math.sin(lt * 1.7 + 1.0)
            layer.alpha_composite(Image.new("RGBA", (W, H), (255, 170, 60, int(10 * fl))))
        draw_label(layer, self.s["series_label"])
        for ln in sc["lines"]:
            if "bubble" in ln and ln["t0"] - 0.15 <= lt <= ln["t1"] + 0.35:
                k = min((lt - ln["t0"] + 0.15) / 0.28, (ln["t1"] + 0.35 - lt) / 0.2, 1.0)
                draw_bubble(layer, ln["who"], ln["bubble"], k)
        caps = [ln for ln in sc["lines"] if "caption" in ln]
        if caps:
            draw_caption(layer, caps[0]["caption"], min((lt - 0.3) / 0.5, (sc["length"] - lt) / 0.3, 1.0))
        if sc.get("title_card"):
            t0 = sc["lines"][-1]["t1"] + 0.2
            if lt >= t0:
                draw_card(layer, self.s["series_label"], self.s["title"], (lt - t0) / 0.5)
        if sc.get("end_card"):
            t0 = sc["lines"][-1]["t1"] + 0.3
            if lt >= t0:
                draw_card(layer, self.s["title"], sc["end_card"], (lt - t0) / 0.5, y=820)
        return layer.convert("RGB")

    def frame(self, t):
        for i, sc in enumerate(self.scenes):
            if t < sc["start"] + sc["length"] or i == len(self.scenes) - 1:
                break
        img = self.scene_frame(sc, t - sc["start"])
        nxt = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
        end = sc["start"] + sc["length"]
        if nxt and t > end - XF:
            k = smooth((t - (end - XF)) / XF)
            img = Image.blend(img, self.scene_frame(nxt, 0.0), k)
        f = min(t / 0.4, (self.total - t) / 0.6, 1.0)
        if f < 1:
            img = Image.blend(Image.new("RGB", (W, H), (8, 12, 26)), img, max(0.0, f))
        return img

    def mix_audio(self, out):
        args = ["ffmpeg", "-v", "error", "-y"]
        flt = []
        for i, (t, a) in enumerate(self.clips):
            args += ["-i", a]
            ms = int(t * 1000)
            flt.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,adelay={ms}|{ms}[a{i}]")
        flt.append("".join(f"[a{i}]" for i in range(len(self.clips))) +
                   f"amix=inputs={len(self.clips)}:normalize=0,apad,atrim=0:{self.total:.3f}[out]")
        args += ["-filter_complex", ";".join(flt), "-map", "[out]", "-ar", "44100", out]
        subprocess.check_call(args)


def main():
    ep = sys.argv[1].rstrip("/")
    e = Episode(ep)
    print("duration %.1fs, %d scenes" % (e.total, len(e.scenes)))
    if "--check" in sys.argv:
        os.makedirs(os.path.join(ep, "check"), exist_ok=True)
        for sc in e.scenes:
            lt = sc["lines"][0]["t0"] + 0.8
            if sc.get("end_card") or sc.get("title_card"):
                lt = sc["length"] - 0.4
            e.scene_frame(sc, lt).save(os.path.join(ep, "check", "scene%02d.jpg" % sc["id"]), quality=80)
        return
    wav = os.path.join(ep, "mix.wav"); e.mix_audio(wav)
    out = os.path.join(ep, "episode.mp4"); tmp = out + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                          "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", tmp],
                         stdin=subprocess.PIPE)
    n = int(e.total * FPS)
    for i in range(n):
        p.stdin.write(e.frame(i / FPS).tobytes())
        if i % 600 == 0:
            print("frame", i, "/", n, flush=True)
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg failed")
    os.replace(tmp, out); os.remove(wav)
    print("ok", out, "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
