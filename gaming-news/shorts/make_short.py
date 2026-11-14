#!/usr/bin/env python3
"""Level Up daily gaming-news Short renderer — TECH style v2 (1080x1920, 30 fps).

Look (owner's request 2026-11-15): full-screen tech HUD. Every story is its own
"page" with its own accent colour (Nintendo red, PlayStation blue, Xbox green…),
over an animated solar-panel / photovoltaic grid background, HUD corner
brackets, monospace data readouts, typewriter headline and a glitch-scan
transition between pages.

Usage:
  python3 make_short.py <episode_dir> --check     # writes check_*.png stills, no video
  python3 make_short.py <episode_dir>             # renders <episode_dir>/short.mp4

<episode_dir>/short.json:
{
  "date_label": "nov 15",
  "stories": [                      # 2-4 stories, biggest first
    {"tag": "GTA 6",                 # page label, <= 9 chars
     "cat": "games",                 # games | nintendo | playstation | xbox | pc | hardware | esports | deals | tech
     "head": "Headline in my own words (<= 90 chars)",
     "src": "source: IGN",
     "audio": "audio/s0.mp3",        # voiceover for this story (story 0 also carries the hook line)
     "art": {...}}                    # see ART TYPES below
  ],
  "outro": {"head": "Which one surprised you most?", "audio": "audio/outro.mp3"}
}
ART TYPES (all text in English, short):
  {"type":"image","file":"img/s0.jpg","label":"optional chip"}           article image, scan overlay, slow push-in
  {"type":"progress","label":"PRE-LOADING","title":"GTA 6","badge":"NOV 19"}
  {"type":"counter","from":1999,"to":9400,"prefix":"$","suffix":"","title":"RTX 5090","sub":"cheapest in the US","badge":"+262% MSRP"}
  {"type":"bars","title":"GPU units on Amazon US","items":[["AMD",9200],["NVIDIA",8900]],"badge":"FIRST TIME EVER"}
  {"type":"pills","title":"NINTENDO DIRECT","items":["2D METROID","MARIO KART WORLD","KIRBY"]}
  {"type":"stat","value":"20M","label":"players in 48 hours","badge":"RECORD"}
  {"type":"split","left":"OFF","right":"DLSS 5"}
"""
import sys, os, math, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.join(HERE, "fonts")
# layout (Shorts safe zone: keep key text between y≈230 and y≈1480)
CX0, CY0, CX1, CY1 = 60, 500, 1020, 1040          # the "monitor" card
CW, CHH = CX1 - CX0, CY1 - CY0
_fc = {}
def _font(file, size, wght=None):
    k = (file, size, wght)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FDIR, file), size)
        if wght: f.set_variation_by_axes([wght])
        _fc[k] = f
    return _fc[k]
fOrb = lambda s, w=800: _font("Orbitron-VF.ttf", s, w)          # big numbers / titles
fMono = lambda s, w=500: _font("JetBrainsMono-VF.ttf", s, w)     # HUD readouts
fRaj = lambda s: _font("Rajdhani-Bold.ttf", s)                    # headline
fRajS = lambda s: _font("Rajdhani-SemiBold.ttf", s)

CYAN = (0, 225, 255)
WHITE = (240, 248, 255)
DIM = (120, 150, 175)
ACC = {"games": (255, 150, 30), "nintendo": (255, 40, 50), "playstation": (40, 130, 255), "xbox": (60, 220, 70),
       "pc": (150, 255, 60), "hardware": (150, 255, 60), "esports": (190, 90, 255), "deals": (255, 205, 40),
       "tech": (0, 225, 255)}
CATNAME = {"games": "GAMES", "nintendo": "NINTENDO", "playstation": "PLAYSTATION", "xbox": "XBOX", "pc": "PC",
           "hardware": "HARDWARE", "esports": "ESPORTS", "deals": "DEALS", "tech": "TECH"}
T_TR = 0.45

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def acc_of(cat): return ACC.get(cat, CYAN)

def text_a(im, xy, txt, f, fill, anchor="la"):
    """Text with real alpha on an RGB image."""
    a = fill[3] if len(fill) == 4 else 255
    if a <= 0: return
    if a >= 255: ImageDraw.Draw(im).text(xy, txt, font=f, fill=fill[:3], anchor=anchor); return
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).text(xy, txt, font=f, fill=a, anchor=anchor)
    im.paste(Image.new("RGB", im.size, fill[:3]), (0, 0), m)

def glow_text(im, xy, txt, f, col, alpha=1.0, blur=18, anchor="ma"):
    if alpha <= 0: return
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).text(xy, txt, font=f, fill=int(255 * alpha), anchor=anchor)
    g = m.filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.new("RGB", im.size, col), (0, 0), g)
    im.paste(Image.new("RGB", im.size, WHITE), (0, 0), m)

def fit(d, txt, f_of, size, maxw):
    while size > 20 and d.textlength(txt, font=f_of(size)) > maxw: size -= 2
    return f_of(size)

def brackets(d, box, col, L=46, w=5):
    x0, y0, x1, y1 = box
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=col, width=w)

def chip(d, x1, y, txt, col, q, right=True):
    if q <= 0: return
    f = fMono(28, 700); tw = d.textlength(txt, font=f)
    x0 = x1 - tw - 40 if right else x1; xa = x0 + tw + 40
    yy = y + (1 - q) * 24
    d.polygon([(x0 + 12, yy), (xa, yy), (xa, yy + 50 - 12), (xa - 12, yy + 50), (x0, yy + 50), (x0, yy + 12)],
              fill=col + (int(235 * q),))
    d.text(((x0 + xa) / 2, yy + 25), txt, font=f, fill=(5, 10, 20, int(255 * q)), anchor="mm")

# ---------------- solar-panel background ----------------
def _persp_coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

_pv = {}
def pv_texture():
    """Flat photovoltaic array: panels of 6x10 mono cells, silver frames, busbars."""
    if "t" in _pv: return _pv["t"]
    TW, TH = 4200, 5200
    rng = np.random.default_rng(7)
    im = Image.new("RGB", (TW, TH), (55, 62, 72)); d = ImageDraw.Draw(im)
    cell = 40; gap = 2; pcols, prows = 6, 10; frame = 8; pgap = 26
    pw = pcols * cell + frame * 2; ph = prows * cell + frame * 2
    y = 0
    while y < TH:
        x = 0
        while x < TW:
            d.rectangle([x, y, x + pw, y + ph], fill=(150, 160, 172))           # aluminium frame
            d.rectangle([x + frame - 2, y + frame - 2, x + pw - frame + 2, y + ph - frame + 2], fill=(18, 26, 44))
            tone = rng.uniform(0.85, 1.15)
            for r in range(prows):
                for c in range(pcols):
                    cx = x + frame + c * cell; cy = y + frame + r * cell
                    b = tone * rng.uniform(0.9, 1.1)
                    d.rectangle([cx + gap, cy + gap, cx + cell - gap, cy + cell - gap],
                                fill=(int(16 * b), int(42 * b), int(92 * b)))
                    # cut corners of mono cells
                    k = 7
                    for (px, py) in ((cx + gap, cy + gap), (cx + cell - gap, cy + gap), (cx + gap, cy + cell - gap), (cx + cell - gap, cy + cell - gap)):
                        d.polygon([(px, py), (px + (k if px < cx + cell / 2 else -k), py), (px, py + (k if py < cy + cell / 2 else -k))], fill=(18, 26, 44))
                    # busbars + fingers
                    for bx in (0.33, 0.66):
                        d.line([(cx + cell * bx, cy + gap), (cx + cell * bx, cy + cell - gap)], fill=(110, 125, 150), width=1)
            x += pw + pgap
        y += ph + pgap
    _pv["t"] = im
    return im

_bgc = {}
def page_bg(cat, seed):
    """Perspective solar field, tinted with the page accent, dark enough for text."""
    k = (cat, seed % 2)
    if k in _bgc: return _bgc[k]
    acc = np.array(acc_of(cat), float)
    tex = pv_texture()
    TW, TH = tex.size
    hz = 360                                      # horizon line
    off = 260 * (seed % 2)
    dst = [(-900, hz), (W + 900, hz), (W + 260, H), (-260, H)]
    src = [(0 + off, 0), (TW - 400 + off, 0), (TW - 400 + off, TH), (0 + off, TH)]
    field = tex.transform((W, H), Image.PERSPECTIVE, _persp_coeffs(dst, src), Image.BILINEAR)
    a = np.asarray(field).astype(np.float32)
    yy = np.arange(H)[:, None].astype(np.float32); xx = np.arange(W)[None, :].astype(np.float32)
    # depth fog toward the horizon + global dim
    depth = np.clip((yy - hz) / (H - hz), 0, 1)
    a = a * (0.25 + 0.55 * depth[..., None] ** 0.7)
    fog = np.exp(-np.clip(yy - hz, 0, None) / 260)[..., None]
    a = a * (1 - fog) + (acc * 0.35 + np.array([10, 20, 40])) * fog
    sky = (yy < hz)[..., None]
    skyc = np.array([4, 8, 18]) + (acc * 0.45) * np.exp(-(hz - yy) / 120)[..., None]
    a = np.where(sky, skyc * np.ones((1, W, 1)), a)
    # horizon glow
    a += acc * 0.9 * np.exp(-np.abs(yy - hz) / 26)[..., None] * np.exp(-((xx - W / 2) / 700) ** 2)[..., None]
    # vignette
    v = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    a *= (1 - 0.9 * v ** 2)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # faint HUD grid + scanlines
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W, 60): d.line([(x, 0), (x, hz)], fill=tuple(int(c) for c in acc) + (14,), width=1)
    for y in range(0, hz, 60): d.line([(0, y), (W, y)], fill=tuple(int(c) for c in acc) + (14,), width=1)
    sl = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sl)
    for y in range(0, H, 4): sd.line([(0, y), (W, y)], fill=26)
    im.paste((0, 0, 0), (0, 0), sl)
    _bgc[k] = im
    return im

_sheen = {}
def sheen_mask():
    """Diagonal light band that sweeps across the panels (reflection)."""
    if "m" in _sheen: return _sheen["m"]
    bw = 700; m = np.zeros((H, bw), np.float32)
    x = np.arange(bw)[None, :]; y = np.arange(H)[:, None]
    m = np.exp(-((x - bw / 2 - (y - H) * 0.35) / 90) ** 2) * np.clip((y - 380) / 900, 0, 1)
    _sheen["m"] = Image.fromarray((m * 70).astype(np.uint8))
    return _sheen["m"]

def sheen_band():
    if "b" in _sheen: return _sheen["b"]
    bw = 2 * W
    x = np.arange(bw)[None, :].astype(np.float32); y = np.arange(H)[:, None].astype(np.float32)
    c = bw / 2 + (y - H / 2) * 0.45
    m = np.exp(-((x - c) / 110) ** 2) * np.clip((y - 380) / 700, 0, 1)
    _sheen["b"] = Image.fromarray((m * 60).astype(np.uint8))
    return _sheen["b"]

# ---------------- art types (drawn on the CW x CHH card) ----------------
def card_base(acc):
    im = Image.new("RGB", (CW, CHH), (4, 10, 22))
    a = np.asarray(im).astype(np.float32)
    yy = np.linspace(0, 1, CHH)[:, None]
    a = a + np.array(acc, float) * 0.10 * (1 - yy)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, CW, 40): d.line([(x, 0), (x, CHH)], fill=acc + (20,), width=1)
    for y in range(0, CHH, 40): d.line([(0, y), (CW, y)], fill=acc + (20,), width=1)
    return im

def art_image(im, t, a, acc, ctx):
    src = ctx["img"]
    z = 1 + 0.06 * (t / 7)
    sw, sh = int(src.width / z), int(src.height / z)
    ox, oy = (src.width - sw) // 2, (src.height - sh) // 2
    pic = src.crop((ox, oy, ox + sw, oy + sh)).resize((CW, CHH), Image.BILINEAR)
    im.paste(pic, (0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    # scan line sweeping down + light scanlines
    sy = int((t * 260) % (CHH + 200)) - 100
    d.rectangle([0, sy, CW, sy + 3], fill=acc + (150,))
    d.rectangle([0, sy - 40, CW, sy], fill=acc + (22,))
    if a.get("label"): chip(d, CW - 24, CHH - 76, a["label"], acc, ease((t - 2.0) / 0.4))

def art_progress(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease((t - 0.3) / 3.0)
    d.text((60, 90), "> " + a.get("label", "LOADING"), font=fMono(34, 600), fill=acc)
    d.text((60, 150), a["title"], font=fit(d, a["title"], fOrb, 92, 620), fill=WHITE)
    d.text((CW - 60, 165), f"{int(p*100):3d}%", font=fOrb(70), fill=acc, anchor="ra")
    n = 24; sx = 60; segw = (CW - 120) / n
    for i in range(n):
        on = i < int(p * n)
        d.rectangle([sx + i * segw + 3, 330, sx + (i + 1) * segw - 3, 390], fill=acc + (230,) if on else (255, 255, 255, 26))
    d.text((60, 420), f"[{'#' * int(p * 20):<20}] {int(p*48.2*10)/10:.1f} GB/s", font=fMono(26), fill=DIM)
    if a.get("badge"): chip(d, CW - 30, 40, a["badge"], acc, ease((t - 3.2) / 0.5))

def art_counter(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease((t - 0.4) / 2.4)
    v = a["from"] + (a["to"] - a["from"]) * p
    s = f"{a.get('prefix','')}{int(v):,}{a.get('suffix','')}" if abs(a["to"]) >= 100 else f"{a.get('prefix','')}{v:.1f}{a.get('suffix','')}"
    d.text((60, 70), "> " + a.get("title", "").upper(), font=fMono(36, 700), fill=acc)
    glow_text(im, (CW // 2, 170), s, fit(d, s, fOrb, 150, CW - 100), acc)
    if a.get("sub"): d.text((CW // 2, 370), a["sub"], font=fRajS(40), fill=WHITE, anchor="ma")
    # sparkline
    pts = [(60 + i * (CW - 120) / 40, 470 - 40 * (i / 40) ** 2 * p - 8 * math.sin(i * 1.7 + t * 3)) for i in range(41)]
    d.line(pts, fill=acc + (200,), width=3)
    if a.get("badge"): chip(d, CW - 30, 40, a["badge"], (255, 70, 70), ease((t - 2.8) / 0.4))

def art_bars(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    d.text((60, 50), "> " + a.get("title", "").upper(), font=fit(d, "> " + a.get("title", "").upper(), lambda s: fMono(s, 700), 34, CW - 120), fill=acc)
    items = a["items"][:4]; mx = max(v for _, v in items); base = 450
    cols = [acc, (255, 255, 255), (255, 70, 70), (255, 205, 40)]
    n = len(items); bw = min(170, (CW - 160) // n - 40)
    xs = [CW / 2 + (i - (n - 1) / 2) * (bw + 70) for i in range(n)]
    for y in range(base, 120, -60): d.line([(40, y), (CW - 40, y)], fill=(255, 255, 255, 22))
    for i, (lab, v) in enumerate(items):
        p = ease((t - 0.4 - i * 0.25) / 2.0); h = 260 * v / mx * p; x = xs[i]; c = cols[i % 4]
        d.rectangle([x - bw / 2, base - h, x + bw / 2, base], fill=c + (60,), outline=c + (255,), width=3)
        for yy in range(int(base - h) + 8, base, 14): d.line([(x - bw / 2 + 6, yy), (x + bw / 2 - 6, yy)], fill=c + (70,))
        d.text((x, base - h - 52), f"{int(v*p):,}", font=fOrb(36), fill=WHITE, anchor="ma")
        d.text((x, base + 18), lab.upper(), font=fMono(28, 700), fill=WHITE, anchor="ma")
    if a.get("badge"): chip(d, CW - 30, 110, a["badge"], acc, ease((t - 2.6) / 0.4))

def art_pills(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    title = a.get("title", "")
    glow_text(im, (CW // 2, 70), title, fit(d, title, fOrb, 72, CW - 100), acc, ease(t / 0.4), blur=14)
    d.line([(80, 180), (CW - 80, 180)], fill=acc + (160,), width=2)
    for i, lab in enumerate(a["items"][:4]):
        q = ease((t - 0.6 - i * 0.45) / 0.35)
        if q <= 0: continue
        y = 220 + i * 76; x = 110 + (1 - q) * 40
        d.rectangle([x - 30, y + 6, x - 8, y + 28], outline=acc + (int(255 * q),), width=3)
        if q > 0.6: d.line([(x - 26, y + 18), (x - 20, y + 25), (x - 10, y + 9)], fill=acc, width=4)
        text_a(im, (x + 14, y), f"{lab}", fRaj(52), WHITE + (int(255 * q),))
        text_a(im, (CW - 90, y + 12), "OK", fMono(28, 700), acc + (int(255 * q),), anchor="ra")

def art_stat(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease((t - 0.15) / 0.6)
    # rotating HUD ring behind the number
    cx, cy, r = CW // 2, 225, 190
    for k in range(36):
        ang = math.radians(k * 10 + t * 30)
        if k % 3 == 0: continue
        d.arc([cx - r, cy - r, cx + r, cy + r], math.degrees(ang), math.degrees(ang) + 6, fill=acc + (int(120 * p),), width=6)
    d.arc([cx - r + 24, cy - r + 24, cx + r - 24, cy + r - 24], -t * 60, -t * 60 + 120, fill=acc + (int(200 * p),), width=3)
    val = a["value"]
    # digit roll-in: characters appear left->right
    shown = val[:max(1, int(len(val) * ease((t - 0.1) / 0.5)))]
    glow_text(im, (cx, 150), shown, fit(d, val, fOrb, int(170 * (0.85 + 0.15 * p)), CW - 80), acc, p)
    q = ease((t - 0.6) / 0.5)
    text_a(im, (cx, 430), a.get("label", ""), fit(d, a.get("label", ""), fRajS, 46, CW - 80), WHITE + (int(255 * q),), anchor="ma")
    if a.get("badge"): chip(d, CW - 30, 40, a["badge"], acc, ease((t - 1.0) / 0.4))

_split = {}
def art_split(im, t, a, acc, ctx):
    if "sharp" not in _split:
        b = pv_texture().crop((0, 0, 1300, 730)).resize((CW, CHH), Image.LANCZOS)
        _split["sharp"] = b
        _split["px"] = b.resize((CW // 18, CHH // 18), Image.BILINEAR).resize((CW, CHH), Image.NEAREST)
    p = 0.25 + 0.5 * ease_io((math.sin(t * 1.3 - 1.6) + 1) / 2); sx = int(CW * p)
    im.paste(_split["px"].crop((0, 0, sx, CHH)), (0, 0)); im.paste(_split["sharp"].crop((sx, 0, CW, CHH)), (sx, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([sx - 2, 0, sx + 2, CHH], fill=acc)
    chip(d, 30, CHH - 80, a.get("left", "OFF"), (200, 210, 220), 1, right=False)
    chip(d, CW - 30, CHH - 80, a.get("right", "ON"), acc, 1)

def art_outro(im, t, a, acc, ctx):
    d = ImageDraw.Draw(im, "RGBA")
    p = ease(t / 0.6)
    text_a(im, (CW // 2, 110), "> SUBSCRIBE_", fMono(40, 700), acc + (int(255 * p),), anchor="ma")
    glow_text(im, (CW // 2, 200 + (1 - p) * 30), "@LevelUpGamesNews", fit(d, "@LevelUpGamesNews", fOrb, 64, CW - 80), acc, p, blur=14)
    q = ease((t - 0.7) / 0.5)
    chip(d, CW // 2 + 210, 360, "DAILY GAMING NEWS", acc, q)

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
            self.scenes.append(dict(key=f"s{i}", idx=i, data=s, dur=max(dur, 4.0)))
        o = self.cfg.get("outro", {})
        self.scenes.append(dict(key="outro", idx=-1, dur=max(3.0, (self.adur(o.get("audio")) + 0.5) if o.get("audio") else 3.0),
                                data=dict(head=o.get("head", "Which one surprised you most?"), tag="END",
                                          src="follow for daily gaming news", art={"type": "outro"}, cat="tech")))
        self.total = sum(s["dur"] for s in self.scenes)
        self.ctx = []
        for sc in self.scenes:
            a = sc["data"]["art"]; c = {}
            if a["type"] == "image":
                im = Image.open(os.path.join(d, a["file"])).convert("RGB")
                im = ImageOps.fit(im, (int(CW * 1.12), int(CHH * 1.12)), Image.LANCZOS)
                ar = np.asarray(im).astype(np.float32)
                ar = ar * np.array([0.92, 1.0, 1.08]) + np.array([-6, 0, 8])      # cool tech grade
                im = Image.fromarray(np.clip(ar, 0, 255).astype(np.uint8))
                c["img"] = im
            self.ctx.append(c)
        self.lines = {}

    def adur(self, rel):
        if not rel: return 0
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              os.path.join(self.dir, rel)], capture_output=True, text=True).stdout
        return float(out.strip())

    def start(self, si): return sum(s["dur"] for s in self.scenes[:si])

    def wrap(self, si):
        if si in self.lines: return self.lines[si]
        head = self.scenes[si]["data"]["head"]; d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        size = 80
        while True:
            f = fRaj(size); lines, cur = [], ""
            for w in head.split():
                tst = (cur + " " + w).strip()
                if d.textlength(tst, font=f) > 920 and cur: lines.append(cur); cur = w
                else: cur = tst
            lines.append(cur)
            if len(lines) <= 4 or size <= 56: break
            size -= 4
        self.lines[si] = (lines[:4], f, int(size * 1.02))
        return self.lines[si]

    def page(self, si, t):
        """One full-screen page (no transition)."""
        sc = self.scenes[si]; data = sc["data"]; cat = data.get("cat", "games"); acc = acc_of(cat)
        gt = self.start(si) + t; n = len(self.cfg["stories"]); last = sc["idx"] < 0
        cv = page_bg(cat, si).copy()
        # sheen sweeping across the solar panels
        sb = sheen_band(); ox = int(-W * 1.6 + ((gt * 0.22) % 1.0) * W * 2.6)
        tint = Image.new("RGB", (W, H), tuple(min(255, int(c * 0.5 + 120)) for c in acc))
        m = Image.new("L", (W, H), 0); m.paste(sb, (ox, 0)); cv.paste(tint, (0, 0), m)
        d = ImageDraw.Draw(cv, "RGBA")
        # ---- top HUD
        live = int(gt * 2) % 2 == 0
        d.ellipse([60, 252, 80, 272], fill=(255, 50, 50) if live else (90, 20, 20))
        d.text((96, 262), "LEVEL UP // NEWS FEED", font=fMono(28, 700), fill=WHITE, anchor="lm")
        d.text((W - 60, 262), self.cfg.get("date_label", "today").upper() + f"  T+{gt:04.1f}s", font=fMono(26, 500), fill=DIM, anchor="rm")
        # segmented progress (one segment per page, each in its page colour)
        segs = self.scenes; gap = 10; x = 60; sw = (W - 120 - gap * (len(segs) - 1)) / len(segs)
        for k, s2 in enumerate(segs):
            c2 = acc_of(s2["data"].get("cat", "games"))
            st0 = self.start(k); pr = max(0.0, min(1.0, (gt - st0) / s2["dur"]))
            d.rectangle([x, 300, x + sw, 308], fill=(255, 255, 255, 36))
            if pr > 0: d.rectangle([x, 300, x + sw * pr, 308], fill=c2 + (255,))
            x += sw + gap
        # ---- page header
        e = ease(t / 0.35)
        hx = 60 - (1 - e) * 60
        d.polygon([(hx, 372), (hx + 150, 372), (hx + 168, 390), (hx + 168, 452), (hx, 452)], fill=acc + (255,))
        lab = "END" if last else f"{sc['idx']+1:02d}/{n:02d}"
        d.text((hx + 84, 412), lab, font=fOrb(40, 900), fill=(5, 10, 20), anchor="mm")
        name = "LEVEL UP" if last else CATNAME.get(cat, cat.upper())
        text_a(cv, (hx + 196, 412), name, fOrb(54, 800), WHITE + (int(255 * e),), anchor="lm")
        if not last:
            tg = data.get("tag", "").upper()
            tw = d.textlength(tg, font=fMono(30, 700))
            d.rectangle([W - 60 - tw - 36, 386, W - 60, 438], outline=acc + (int(255 * e),), width=3)
            d.text((W - 60 - tw / 2 - 18, 412), tg, font=fMono(30, 700), fill=acc + (int(255 * e),), anchor="mm")
        # ---- monitor card
        card = card_base(acc)
        ARTS[data["art"]["type"]](card, t, data["art"], acc, self.ctx[si])
        cv.paste(card, (CX0, CY0))
        d = ImageDraw.Draw(cv, "RGBA")
        d.rectangle([CX0, CY0, CX1, CY1], outline=acc + (90,), width=2)
        brackets(d, (CX0 - 14, CY0 - 14, CX1 + 14, CY1 + 14), acc + (255,))
        d.text((CX0 + 4, CY1 + 26), f"FEED_{sc['idx']+1 if not last else 0:02d} · {data['art']['type'].upper()}", font=fMono(22, 500), fill=acc + (170,), anchor="lm")
        d.text((CX1 - 4, CY1 + 26), "● REC", font=fMono(22, 700), fill=(255, 60, 60, 220 if live else 90), anchor="rm")
        # hook banner (first story, first ~1.8 s)
        if si == 0:
            q = 1 - ease((t - 1.7) / 0.3)
            if q > 0:
                ban = f"{n} GAMING STORIES // {int(round(self.total))} SEC"
                f = fOrb(44, 900); tw = d.textlength(ban, font=f); y = CY1 - 110 + (1 - ease(t / 0.25)) * 40
                d.rectangle([W / 2 - tw / 2 - 36, y, W / 2 + tw / 2 + 36, y + 84], fill=acc + (int(245 * q),))
                text_a(cv, (W / 2, y + 42), ban, f, (5, 10, 20, int(255 * q)), anchor="mm")
        # ---- headline: typewriter + block cursor
        lines, f, lh = self.wrap(si)
        total_chars = sum(len(l) for l in lines)
        shown = int(total_chars * ease_io((t - 0.25) / 0.9))
        y = 1110; left = shown; cur_xy = None
        for ln in lines:
            part = ln[:max(0, left)]
            if part: d.text((60, y), part, font=f, fill=WHITE)
            if cur_xy is None and left <= len(ln): cur_xy = (60 + d.textlength(part, font=f), y)
            left -= len(ln); y += lh
        if cur_xy and (shown < total_chars or int(gt * 2.5) % 2 == 0):
            d.rectangle([cur_xy[0] + 8, cur_xy[1] + 12, cur_xy[0] + 28, cur_xy[1] + lh - 16], fill=acc)
        q = ease((t - 0.9) / 0.4)
        text_a(cv, (60, y + 22), "> " + data.get("src", "").upper(), fMono(30, 600), DIM + (int(255 * q),))
        return cv

    def frame(self, si, t):
        cur = self.page(si, t)
        if si == 0 or t >= T_TR: return cur
        prev = self.page(si - 1, self.scenes[si - 1]["dur"] + t)
        p = ease_io(t / T_TR); by = int(H * p)
        out = prev.copy(); out.paste(cur.crop((0, 0, W, by)), (0, 0))
        rng = np.random.default_rng(int(t * 1000) + si)
        acc = acc_of(self.scenes[si]["data"].get("cat", "games"))
        # glitch slices around the scan bar
        for _ in range(7):
            y0 = int(by + rng.integers(-260, 260)); hh = int(rng.integers(8, 46)); dx = int(rng.integers(-70, 70))
            y0 = max(0, min(H - hh, y0))
            sl = out.crop((0, y0, W, y0 + hh)); out.paste(sl, (dx, y0))
        # RGB split near the bar
        r, g, b = out.split()
        out = Image.merge("RGB", (ImageChops.offset(r, 8, 0), g, ImageChops.offset(b, -8, 0))) if 0.1 < p < 0.9 else out
        d = ImageDraw.Draw(out, "RGBA")
        d.rectangle([0, by - 4, W, by + 4], fill=acc + (255,))
        d.rectangle([0, by - 60, W, by - 4], fill=acc + (40,))
        return out

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
