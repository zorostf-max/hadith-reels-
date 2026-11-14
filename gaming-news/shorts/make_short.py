#!/usr/bin/env python3
"""Level Up daily gaming-news Short renderer (1080x1920, 30 fps).

Usage:
  python3 make_short.py <episode_dir> --check     # writes check_*.png stills, no video
  python3 make_short.py <episode_dir>             # renders <episode_dir>/short.mp4

<episode_dir>/short.json:
{
  "date_label": "nov 15",
  "stories": [                      # 2-4 stories, biggest first
    {"tag": "GTA 6",                 # chip label, <= 9 chars
     "cat": "games",                 # games | nintendo | playstation | xbox | pc | hardware | esports | deals | tech
     "head": "Headline in my own words (<= 90 chars)",
     "src": "source: IGN",
     "audio": "audio/s0.mp3",        # voiceover for this story (story 0 also carries the hook line)
     "art": {...}}                    # see ART TYPES below
  ],
  "outro": {"head": "Which one surprised you most?", "audio": "audio/outro.mp3"}
}
ART TYPES (all text in English, short):
  {"type":"image","file":"img/s0.jpg","label":"optional chip"}           article image, slow push-in
  {"type":"progress","label":"PRE-LOADING","title":"GTA 6","badge":"NOV 19"}
  {"type":"counter","from":1999,"to":9400,"prefix":"$","suffix":"","title":"RTX 5090","sub":"cheapest in the US","badge":"+262% MSRP"}
  {"type":"bars","title":"GPU units on Amazon US","items":[["AMD",9200],["NVIDIA",8900]],"badge":"FIRST TIME EVER"}
  {"type":"pills","title":"NINTENDO DIRECT","items":["2D METROID","MARIO KART WORLD","KIRBY"]}
  {"type":"stat","value":"20M","label":"players in 48 hours","badge":"RECORD"}
  {"type":"split","left":"OFF","right":"DLSS 5"}
"""
import sys, os, math, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H, FPS = 1080, 1920, 30
PW, PH = 1080, 608
PY = 520                       # panel top (kept inside the Shorts/Reels safe zone)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + name, size)
    return _fc[k]
fB = lambda s: font("Inter-Bold.otf", s)
fXB = lambda s: font("Inter-ExtraBold.otf", s)
fSB = lambda s: font("Inter-SemiBold.otf", s)
fM = lambda s: font("Inter-Medium.otf", s)
ORANGE = (255, 150, 40)
HUES = {"games": (255, 120, 40), "nintendo": (255, 70, 70), "playstation": (60, 120, 255), "xbox": (90, 200, 80),
        "pc": (120, 220, 60), "hardware": (120, 220, 60), "esports": (200, 90, 255), "deals": (255, 200, 40),
        "tech": (90, 200, 255)}
T_TR = 0.42

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def rr(d, box, r, **k): d.rounded_rectangle(box, r, **k)

def ctext(d, cx, y, txt, f, fill, anchor="ma"):
    """Text that respects alpha on RGB images."""
    if len(fill) == 4 and fill[3] < 255:
        if fill[3] <= 0: return
        im = d._image
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).text((cx, y), txt, font=f, fill=fill[3], anchor=anchor)
        im.paste(Image.new(im.mode, im.size, fill[:3]), (0, 0), m)
        return
    d.text((cx, y), txt, font=f, fill=fill, anchor=anchor)

def fit(d, txt, size, maxw, fn=fXB):
    while size > 20 and d.textlength(txt, font=fn(size)) > maxw: size -= 2
    return fn(size)

# ---------------- backgrounds ----------------
def sunset_bg(hue, seed):
    w, h = 1200, 676
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    top = np.array([18, 16, 30]); mid = np.array(hue) * 0.9; low = np.array([20, 12, 10])
    hz = 0.55
    a = np.clip(y / hz, 0, 1)
    sky = top * (1 - a[..., None] ** 2) + mid * (a[..., None] ** 2)
    ground = low + (mid * 0.25 - low) * np.clip(1 - (y - hz) / (1 - hz), 0, 1)[..., None] ** 3
    img = np.where((y < hz)[..., None], sky, ground) * np.ones((1, w, 1))
    dd = np.sqrt(((x - 0.62) * 1.8) ** 2 + ((y - hz) * 3.2) ** 2)
    img = img + np.exp(-dd * 3.2)[..., None] * np.array([255, 200, 140]) * 0.85
    v = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2)
    img *= (1 - 0.75 * v ** 2)[..., None]
    img += rng.normal(0, 4, (h, w, 1))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    hy = int(h * hz); vx = int(w * 0.62)
    for k in range(-9, 10): d.line([(vx, hy), (vx + k * 260, h)], fill=(255, 210, 160, 34), width=2)
    for j in range(1, 9):
        yy = hy + (h - hy) * (j / 9) ** 2
        d.line([(0, yy), (w, yy)], fill=(255, 210, 160, 22), width=2)
    return im

def image_bg(path):
    im = Image.open(path).convert("RGB")
    im = ImageOps.fit(im, (1200, 676), Image.LANCZOS)
    # warm cinematic grade + vignette, like the reference reel
    a = np.asarray(im).astype(np.float32)
    a = a * np.array([1.06, 1.0, 0.9]) + np.array([8, 2, -6])
    y = np.linspace(0, 1, 676)[:, None]; x = np.linspace(0, 1, 1200)[None, :]
    v = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2)
    a *= (1 - 0.6 * v ** 2)[..., None]
    a[int(676 * 0.62):] *= np.linspace(1, 0.55, 676 - int(676 * 0.62))[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ---------------- art types (drawn on the 1080x608 panel) ----------------
def badge(d, x1, y, txt, q, col=ORANGE, tcol=(30, 15, 0)):
    f = fB(28); tw = d.textlength(txt, font=f)
    rr(d, [x1 - tw - 44, y - (1 - q) * 30, x1, y + 58 - (1 - q) * 30], 29, fill=col + (int(240 * q),))
    ctext(d, x1 - tw / 2 - 22, y + 13 - (1 - q) * 30, txt, f, tcol + (int(255 * q),))

def art_image(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    if a.get("label"):
        q = ease((t - 0.5) / 0.4)
        badge(d, 1000, 470, a["label"], q)

def art_progress(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease((t - 0.3) / 3.0)
    rr(d, [190, 150, 890, 450], 34, fill=(10, 10, 14, 170), outline=(255, 255, 255, 70), width=2)
    d.text((240, 190), a.get("label", "LOADING"), font=fSB(30), fill=(255, 220, 190))
    d.text((240, 232), a["title"], font=fit(d, a["title"], 96, 430), fill=(255, 255, 255))
    d.text((840, 200), f"{int(p*100)}%", font=fXB(60), fill=ORANGE, anchor="ra")
    rr(d, [240, 370, 840, 396], 13, fill=(255, 255, 255, 40))
    if p > 0.01: rr(d, [240, 370, 240 + int(600 * p), 396], 13, fill=ORANGE)
    if a.get("badge"): badge(d, 900, 100, a["badge"], ease((t - 3.2) / 0.5))

def art_counter(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    x0, y0 = 118, 220
    rr(d, [x0, y0, x0 + 470, y0 + 200], 24, fill=(22, 22, 26), outline=(140, 220, 80, 160), width=3)
    for i in range(3):
        cx, cy, r = x0 + 85 + i * 150, y0 + 100, 66
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(35, 35, 40), outline=(90, 90, 100), width=3)
        for b in range(7):
            ang = t * 9 + b * 2 * math.pi / 7 + i
            d.line([(cx, cy), (cx + 56 * math.cos(ang), cy + 56 * math.sin(ang))], fill=(120, 120, 130), width=8)
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(140, 220, 80))
    d.text((x0, y0 + 215), a.get("title", ""), font=fB(34), fill=(255, 255, 255))
    p = ease((t - 0.4) / 2.4)
    v = a["from"] + (a["to"] - a["from"]) * p
    s = f"{a.get('prefix','')}{int(v):,}{a.get('suffix','')}" if abs(a["to"]) >= 100 else f"{a.get('prefix','')}{v:.1f}{a.get('suffix','')}"
    d.text((950, 190), s, font=fit(d, s, 76, 330), fill=ORANGE, anchor="ra")
    if a.get("sub"): d.text((950, 286), a["sub"], font=fB(30), fill=(255, 255, 255), anchor="ra")
    if a.get("badge"): badge(d, 950, 350, a["badge"], ease((t - 2.8) / 0.4), col=(230, 50, 50), tcol=(255, 255, 255))

def art_bars(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    ctext(d, 540, 100, a.get("title", ""), fSB(30), (255, 235, 215))
    items = a["items"][:3]; mx = max(v for _, v in items); base = 500
    cols = [(235, 50, 45), (118, 185, 0), (60, 140, 255)]
    n = len(items); xs = [(460 if a.get("badge") else 540) + (i - (n - 1) / 2) * 280 for i in range(n)]
    for i, (lab, v) in enumerate(items):
        p = ease((t - 0.4 - i * 0.25) / 2.0)
        h = 250 * v / mx * p; x = xs[i]
        rr(d, [x - 80, base - h, x + 80, base], 14, fill=cols[i % 3] + (235,))
        d.text((x, base - h - 56), f"{int(v*p):,}", font=fXB(42), fill=(255, 255, 255), anchor="ma")
        d.text((x, base + 16), lab, font=fB(30), fill=(255, 255, 255), anchor="ma")
    if a.get("badge"): badge(d, 1000, 500, a["badge"], ease((t - 2.6) / 0.4))

def art_pills(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = 540, 240; s = 1 + 0.02 * math.sin(t * 2); bw, bh = 520 * s, 230 * s
    rr(d, [cx - bw/2 - 70, cy - bh/2, cx - bw/2 + 10, cy + bh/2], 40, fill=(230, 60, 60))
    rr(d, [cx + bw/2 - 10, cy - bh/2, cx + bw/2 + 70, cy + bh/2], 40, fill=(60, 140, 255))
    rr(d, [cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2], 22, fill=(25, 25, 30), outline=(255, 255, 255, 60), width=2)
    rr(d, [cx - bw/2 + 26, cy - bh/2 + 22, cx + bw/2 - 26, cy + bh/2 - 22], 10, fill=(255, 190, 120))
    ctext(d, cx, cy - 30, a.get("title", ""), fit(d, a.get("title", ""), 60, 420), (40, 20, 10))
    items = a["items"][:3]; f = fB(28)
    widths = [d.textlength(x, font=f) + 44 for x in items]; gap = 24
    x = 540 - (sum(widths) + gap * (len(items) - 1)) / 2
    for i, lab in enumerate(items):
        q = ease((t - 0.6 - i * 0.45) / 0.4); y = 430 + (1 - q) * 30
        rr(d, [x, y, x + widths[i], y + 56], 28, fill=(255, 255, 255, int(45 * q)), outline=(255, 255, 255, int(120 * q)), width=2)
        ctext(d, x + widths[i] / 2, y + 13, lab, f, (255, 255, 255, int(255 * q)))
        x += widths[i] + gap

def art_stat(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease((t - 0.2) / 0.6); s = 0.8 + 0.2 * p
    f = fit(d, a["value"], int(190 * s), 900)
    glow = Image.new("L", im.size, 0)
    ImageDraw.Draw(glow).text((540, 120), a["value"], font=f, fill=int(255 * p), anchor="ma")
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    im.paste(Image.new("RGB", im.size, ORANGE), (0, 0), glow)
    ctext(d, 540, 120, a["value"], f, (255, 255, 255, int(255 * p)))
    q = ease((t - 0.6) / 0.5)
    ctext(d, 540, 390, a.get("label", ""), fSB(40), (255, 230, 210, int(255 * q)))
    if a.get("badge"): badge(d, 990, 40, a["badge"], ease((t - 1.2) / 0.4))

_split = {}
def art_split(im, t, a):
    if "sharp" not in _split:
        b = Image.new("RGB", (PW, PH)); bd = ImageDraw.Draw(b)
        for yy in range(PH):
            c = int(40 + 140 * yy / PH); bd.line([(0, yy), (PW, yy)], fill=(20, c // 2, c))
        rng = np.random.default_rng(3)
        for k in range(14):
            x = rng.integers(0, PW); w = rng.integers(60, 180); h = rng.integers(120, 380)
            bd.polygon([(x - w, PH), (x, PH - h), (x + w, PH)], fill=(15, 20 + k * 4, 50 + k * 6))
        for k in range(60):
            x, y = rng.integers(0, PW), rng.integers(0, PH // 2); bd.ellipse([x, y, x + 4, y + 4], fill=(220, 240, 255))
        bd.ellipse([700, 90, 860, 250], fill=(160, 220, 255))
        _split["sharp"] = b
        _split["px"] = b.resize((PW // 18, PH // 18), Image.BILINEAR).resize((PW, PH), Image.NEAREST)
    p = 0.25 + 0.5 * ease_io((math.sin(t * 1.3 - 1.6) + 1) / 2); sx = int(PW * p)
    im.paste(_split["px"].crop((0, 0, sx, PH)), (0, 0)); im.paste(_split["sharp"].crop((sx, 0, PW, PH)), (sx, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([sx - 3, 0, sx + 3, PH], fill=(255, 255, 255))
    d.ellipse([sx - 30, PH // 2 - 30, sx + 30, PH // 2 + 30], fill=(255, 255, 255))
    rr(d, [40, 470, 220, 526], 28, fill=(0, 0, 0, 140)); ctext(d, 130, 482, a.get("left", "OFF"), fB(28), (255, 255, 255))
    rr(d, [830, 470, 1040, 526], 28, fill=(90, 200, 255, 220)); ctext(d, 935, 482, a.get("right", "ON"), fB(28), (5, 20, 35))

def art_outro(im, t, a):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease(t / 0.6)
    ctext(d, 540, 150, "FOLLOW", fSB(44), (255, 220, 180, int(255 * p)))
    ctext(d, 540, 230 + (1 - p) * 30, "@LevelUpGamesNews", fXB(int(76 * (1 + 0.04 * math.sin(t * 5) * (t > 0.8)))), (255, 255, 255, int(255 * p)))
    q = ease((t - 0.7) / 0.5)
    rr(d, [350, 380, 730, 450], 35, fill=(255, 150, 40, int(240 * q)))
    ctext(d, 540, 394, "DAILY GAMING NEWS", fB(30), (30, 15, 0, int(255 * q)))

ARTS = dict(image=art_image, progress=art_progress, counter=art_counter, bars=art_bars, pills=art_pills,
            stat=art_stat, split=art_split, outro=art_outro)

# ---------------- episode ----------------
class Ep:
    def __init__(self, d):
        self.dir = d
        self.cfg = json.load(open(os.path.join(d, "short.json")))
        st = self.cfg["stories"]; n = len(st)
        self.scenes = []
        for i, s in enumerate(st):
            dur = self.adur(s.get("audio")) + 0.35 if s.get("audio") else 5.0
            self.scenes.append(dict(key=f"s{i}", idx=i, data=s, dur=max(dur, 4.0),
                                    kicker=f"{i+1} of {n} · {s.get('cat','games')}"))
        o = self.cfg.get("outro", {})
        self.scenes.append(dict(key="outro", idx=-1, dur=max(3.0, (self.adur(o.get("audio")) + 0.5) if o.get("audio") else 3.0),
                                data=dict(head=o.get("head", "Which one surprised you most?"),
                                          src="follow for daily gaming news", art={"type": "outro"}, cat="games"),
                                kicker="that's today"))
        self.total = sum(s["dur"] for s in self.scenes)
        self.bgs = []
        for i, sc in enumerate(self.scenes):
            a = sc["data"]["art"]
            if a["type"] == "image": self.bgs.append(image_bg(os.path.join(d, a["file"])))
            else: self.bgs.append(sunset_bg(HUES.get(sc["data"].get("cat"), (255, 150, 40)), i))
        self.chips = [self.chips_overlay(i) for i in range(n)] + [self.chips_overlay(-1)]
        self.tcache = {}

    def adur(self, rel):
        if not rel: return 0
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              os.path.join(self.dir, rel)], capture_output=True, text=True).stdout
        return float(out.strip())

    def start(self, si): return sum(s["dur"] for s in self.scenes[:si])

    def chips_overlay(self, active):
        st = self.cfg["stories"]; n = len(st)
        im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im, "RGBA")
        gap = 12; cw = min(240, (PW - 60 - gap * (n - 1)) // n)
        x = (PW - (n * cw + (n - 1) * gap)) // 2
        for i, s in enumerate(st):
            on = i == active
            rr(d, [x, 22, x + cw, 78], 16, fill=(255, 150, 40, 235) if on else (255, 255, 255, 34),
               outline=(255, 255, 255, 0 if on else 80), width=2)
            lab = f"{i+1:02d} {s['tag']}"
            d.text((x + cw / 2, 50), lab, font=fit(d, lab, 26, cw - 20, fSB),
                   fill=(25, 12, 0) if on else (255, 255, 255, 210), anchor="mm")
            x += cw + gap
        return im

    def panel(self, si, t):
        sc = self.scenes[si]; bg = self.bgs[si]
        z = 1 + 0.07 * (t / 7)
        cw, ch = int(1200 / z / 1.111), int(676 / z / 1.111)
        im = bg.crop((600 - cw // 2, 338 - ch // 2, 600 + cw // 2, 338 + ch // 2)).resize((PW, PH), Image.BILINEAR)
        a = sc["data"]["art"]
        ARTS[a["type"]](im, t, a)
        return im

    def text_layer(self, si):
        if si in self.tcache: return self.tcache[si]
        data = self.scenes[si]["data"]
        im = Image.new("RGBA", (W, 460), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        f = fB(62); lines, cur = [], ""
        for w in data["head"].split():
            tst = (cur + " " + w).strip()
            if d.textlength(tst, font=f) > 880 and cur: lines.append(cur); cur = w
            else: cur = tst
        lines.append(cur)
        y = 0
        for ln in lines[:4]:
            d.text((W // 2, y), ln, font=f, fill=(255, 255, 255), anchor="ma"); y += 78
        d.text((W // 2, y + 30), data.get("src", ""), font=fM(32), fill=(170, 170, 175), anchor="ma")
        self.tcache[si] = im
        return im

    def frame(self, si, t):
        sc = self.scenes[si]; dur = sc["dur"]; gt = self.start(si) + t; last = si == len(self.scenes) - 1
        cv = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(cv, "RGBA")
        # brand row
        rr(d, [W // 2 - 170, 330, W // 2 + 170, 386], 28, outline=(255, 255, 255, 70), width=2)
        d.ellipse([W // 2 - 142, 350, W // 2 - 126, 366], fill=(255, 60, 50) if int(gt * 2) % 2 == 0 else (120, 30, 25))
        d.text((W // 2 + 12, 358), f"LEVEL UP · {self.cfg.get('date_label','today').upper()}", font=fSB(26), fill=(255, 255, 255, 220), anchor="mm")
        # panel + swap transition
        p_tr = ease_io(t / T_TR) if si > 0 else 1.0
        cur = self.panel(si, t)
        if p_tr < 1:
            prev = self.panel(si - 1, self.scenes[si - 1]["dur"] + t)
            off = int(PW * p_tr); pan = Image.new("RGB", (PW, PH))
            if off < PW: pan.paste(prev.crop((off, 0, PW, PH)), (0, 0))
            if off > 0: pan.paste(cur.crop((0, 0, off, PH)), (PW - off, 0))
            fl = int(110 * math.sin(math.pi * p_tr))
            pan = Image.blend(pan, Image.new("RGB", (PW, PH), (255, 255, 255)), fl / 255)
            cur = pan
        n = len(self.cfg["stories"])
        if sc["idx"] >= 0:
            idx = sc["idx"] - (1 if (si > 0 and p_tr < 0.5) else 0)
        else:
            idx = n - 1 if p_tr < 0.5 else -1
        ch = self.chips[idx]
        cur.paste(ch, (0, 0), ch)
        cv.paste(cur, (0, PY))
        # hook banner on the first second of the first story
        if si == 0:
            q = 1 - ease((t - 1.6) / 0.3)
            if q > 0:
                ban = f"{n} GAMING STORIES · {int(round(self.total))} SEC"
                f = fXB(44); tw = d.textlength(ban, font=f)
                y = PY + PH - 125 + (1 - ease(t / 0.25)) * 40
                rr(d, [W / 2 - tw / 2 - 36, y, W / 2 + tw / 2 + 36, y + 84], 42, fill=(255, 150, 40, int(245 * q)))
                ctext(d, W / 2, y + 18, ban, f, (25, 12, 0, int(255 * q)))
        # timeline
        d.rectangle([0, PY + PH, W, PY + PH + 6], fill=(255, 255, 255, 40))
        d.rectangle([0, PY + PH, int(W * gt / self.total), PY + PH + 6], fill=ORANGE)
        # arrows (right one "pressed" before each swap)
        pr = 0.0
        if not last: pr = max(0, 1 - abs(t - (dur - 0.08)) / 0.18)
        if si > 0 and t < 0.12: pr = max(pr, 1 - t / 0.12)
        for side in ("l", "r"):
            prs = pr if side == "r" else 0
            cx = 64 if side == "l" else PW - 64; cy = PY + PH // 2 + 20
            r = 40 * (1 - 0.18 * prs)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, int(40 + 160 * prs)), outline=(255, 255, 255, 110), width=2)
            k = 12 * (1 - 0.18 * prs); sg = -1 if side == "l" else 1
            d.line([(cx - sg * k * 0.5, cy - k), (cx + sg * k * 0.6, cy), (cx - sg * k * 0.5, cy + k)],
                   fill=(20, 20, 20) if prs > 0.5 else (255, 255, 255), width=5, joint="curve")
        # kicker
        a_in = ease((t - (0.15 if si else 0)) / 0.35); a_out = 1 if last else 1 - ease((t - (dur - 0.15)) / 0.15)
        ctext(d, W // 2, PY - 86, sc["kicker"], fM(40), (255, 255, 255, int(255 * a_in * a_out)))
        # headline + source
        tl = self.text_layer(si); e = ease((t - 0.2) / 0.4); al = e * a_out
        if al > 0:
            m = tl.getchannel("A").point(lambda v: int(v * al))
            cv.paste(tl.convert("RGB"), (0, PY + PH + 62 + int((1 - e) * 40)), m)
        return cv

    def render(self, out):
        files = []
        for si, sc in enumerate(self.scenes):
            n = int(round(sc["dur"] * FPS)); fn = os.path.join(self.dir, f"_scene{si:02d}.mp4"); tmp = fn[:-4] + ".tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                  "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                                  "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for i in range(n): p.stdin.write(self.frame(si, i / FPS).tobytes())
            p.stdin.close()
            if p.wait() != 0: sys.exit("ffmpeg failed on scene %d" % si)
            os.replace(tmp, fn); files.append(fn)
        # exact total from frame counts
        self.total = sum(round(s["dur"] * FPS) / FPS for s in self.scenes)
        lst = os.path.join(self.dir, "_list.txt")
        open(lst, "w").write("".join(f"file '{os.path.basename(f)}'\n" for f in files))
        vid = os.path.join(self.dir, "_video.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
        music = os.path.join(self.dir, "_music.wav"); self.make_music(music)
        # voice clips placed at their scene starts, music ducked underneath
        inputs = ["-i", vid, "-i", music]; filt = []; labels = []
        starts = [0.0]
        for s in self.scenes[:-1]: starts.append(starts[-1] + round(s["dur"] * FPS) / FPS)
        vi = 2
        clips = [(sc["data"].get("audio") if sc["idx"] >= 0 else self.cfg.get("outro", {}).get("audio")) for sc in self.scenes]
        for k, c in enumerate(clips):
            if not c: continue
            inputs += ["-i", os.path.join(self.dir, c)]
            ms = int((starts[k] + (0.25 if k else 0.05)) * 1000)
            filt.append(f"[{vi}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.0[v{vi}]"); labels.append(f"[v{vi}]"); vi += 1
        filt.append(f"[1:a]volume={0.22 if labels else 0.9}[m]")
        filt.append(f"[m]{''.join(labels)}amix=inputs={len(labels)+1}:normalize=0:duration=first,volume=2.0,alimiter=limit=0.95[a]")
        tmp = out[:-4] + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, out)
        for f in files + [lst, vid, music]: os.remove(f)

    def make_music(self, path):
        sr = 44100; n = int((self.total + 0.5) * sr); a = np.zeros(n); rng = np.random.default_rng(1)
        beat = 60 / 112
        tt = np.arange(int(0.35 * sr)) / sr
        kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
        ht = np.arange(int(0.05 * sr)) / sr; hat = np.diff(rng.normal(0, 1, len(ht)) * np.exp(-ht * 90), prepend=0)
        notes = [55, 55, 65.4, 49]; k = 0
        while k * beat < self.total:
            s = int(k * beat * sr)
            if s + len(kick) < n: a[s:s + len(kick)] += 0.8 * kick
            h = int((k + 0.5) * beat * sr)
            if h + len(hat) < n: a[h:h + len(hat)] += 0.18 * hat
            bt = np.arange(int(beat * sr)) / sr; f = notes[(k // 4) % 4]
            bass = (np.sign(np.sin(2 * np.pi * f * bt)) * 0.5 + np.sin(2 * np.pi * f * bt) * 0.5) * np.exp(-bt * 5) * 0.12
            if s + len(bass) < n: a[s:s + len(bass)] += bass
            k += 1
        ta = np.arange(n) / sr
        a += 0.035 * (np.sin(2 * np.pi * 220 * ta) + np.sin(2 * np.pi * 277.2 * ta) + np.sin(2 * np.pi * 329.6 * ta)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * ta))
        acc = 0
        for s in self.scenes[:-1]:
            acc += round(s["dur"] * FPS) / FPS
            c0 = int((acc - 0.08) * sr); ct = np.arange(int(0.03 * sr)) / sr
            a[c0:c0 + len(ct)] += 1.4 * np.sin(2 * np.pi * 2400 * ct) * np.exp(-ct * 250)
            wl = int(0.5 * sr); wt = np.arange(wl) / wl; cs = np.cumsum(rng.normal(0, 1, wl))
            win = (40 * (1 - wt) + 3).astype(int); idx = np.arange(wl); lo = np.maximum(0, idx - win)
            o = (cs - cs[lo]) / np.maximum(1, idx - lo)
            s0 = int((acc - 0.2) * sr); a[s0:s0 + wl] += 2.2 * o * np.sin(np.pi * wt) ** 2
        a = a / np.max(np.abs(a)) * 0.89
        fade = int(0.8 * sr); a[-fade:] *= np.linspace(1, 0, fade)
        st = (np.stack([a, a], 1) * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())

if __name__ == "__main__":
    d = sys.argv[1]; ep = Ep(d)
    if "--check" in sys.argv:
        shots = []
        for si, sc in enumerate(ep.scenes):
            for t in (0.2 if si else 0.6, sc["dur"] * 0.7):
                shots.append(ep.frame(si, t).resize((360, 640)))
        cols = 4; rows = math.ceil(len(shots) / cols)
        sheet = Image.new("RGB", (360 * cols, 640 * rows))
        for i, s in enumerate(shots): sheet.paste(s, ((i % cols) * 360, (i // cols) * 640))
        sheet.save(os.path.join(d, "check_sheet.png"))
        ep.frame(0, 0.6).save(os.path.join(d, "check_full.png"))
        print("check:", os.path.join(d, "check_sheet.png"), "total %.1fs" % ep.total)
    else:
        ep.render(os.path.join(d, "short.mp4"))
        print("rendered", os.path.join(d, "short.mp4"), "%.1fs" % ep.total)
