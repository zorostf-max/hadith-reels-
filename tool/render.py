"""Render a hadith reel from a data JSON file (also writes <output>.cover.jpg, the thumbnail with the hook question).

Usage:  python3 render.py path/to/data.json path/to/output.mp4 [--theme morning|noon|night] [--check]
Background follows the publishing time: "theme" in the data file (morning = 08:00, noon = 13:00,
night = 20:00; default night), or --theme to override it. The data file follows the schema in README.md. Output: 1080x1920, 30 fps,
H.264 + AAC, kept under ~18 MB so Telegram can fetch it by URL. Sound: the per-scene narration clips in
"narration" (each scene is stretched to fit its clip); otherwise silent ("audio": "ambience" is rejected by the owner).
"""
import sys, os, json, asyncio, subprocess, shutil, tempfile
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
CHROME = shutil.which("google-chrome") or shutil.which("chromium")


async def chunk(work, idx, t0, t1, out):
    tmp = out + ".tmp.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                           "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if CHROME:
            kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(work, "index.html"))
        for f in range(round(t0 * FPS), round(t1 * FPS)):
            await pg.evaluate(f"render({f / FPS})")
            ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
        await b.close()
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit(f"chunk {idx} failed")
    os.rename(tmp, out)


async def duration(work):
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if CHROME:
            kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(work, "index.html"))
        d = await pg.evaluate("DUR")
        tl = await pg.evaluate("T")
        await b.close()
        return d, tl


async def stills(work, times, outdir):
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if CHROME:
            kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(work, "index.html"))
        T = await pg.evaluate("T")
        for name, (a, z) in T.items():
            await pg.evaluate(f"render({z - 0.8})")
            await pg.screenshot(path=os.path.join(outdir, f"check_{name}.png"))
        await b.close()


async def cover_still(work, t, out):
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if CHROME:
            kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(work, "index.html"))
        await pg.evaluate(f"render({t})")
        await pg.screenshot(path=out, type="jpeg", quality=90)
        await b.close()


def main():
    data_path, out_path = sys.argv[1], os.path.abspath(sys.argv[2])
    check_only = "--check" in sys.argv
    work = tempfile.mkdtemp(prefix="reel_")
    shutil.copy(os.path.join(HERE, "template.html"), os.path.join(work, "index.html"))
    data = json.load(open(data_path, encoding="utf-8"))
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--theme"):
            data["theme"] = arg.split("=", 1)[1] if "=" in arg else sys.argv[i + 1]
    if data.get("theme", "night") not in ("morning", "noon", "night"):
        raise SystemExit("theme must be morning, noon or night")
    # Narration: {"<scene id>": "path/to/clip.mp3", ...} (paths relative to the data file).
    # Each clip starts 0.35 s into its scene; the scene is stretched so the clip ends >= 0.6 s before it does.
    clips = {}
    for sid, rel in (data.get("narration") or {}).items():
        p = rel if os.path.isabs(rel) else os.path.join(os.path.dirname(os.path.abspath(data_path)), rel)
        if not os.path.exists(p):
            raise SystemExit(f"narration clip missing for scene {sid}: {p}")
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                 capture_output=True, text=True, check=True).stdout.strip())
        clips[sid] = (p, d)
        lead = 0.05 if sid == "hook" else 0.35
        need = round(d + lead + 0.6, 2)
        data.setdefault("durations", {})
        data["durations"][sid] = max(data["durations"].get(sid, 0), need)
    with open(os.path.join(work, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA=" + json.dumps(data, ensure_ascii=False) + ";")
    if check_only:
        outdir = os.path.dirname(out_path)
        asyncio.run(stills(work, None, outdir))
        print("stills written to", outdir)
        return
    dur, timeline = asyncio.run(duration(work))
    # Cover image for the reel (the hook question on the full background), used as the Instagram/YouTube thumbnail
    cover = os.path.splitext(out_path)[0] + ".cover.jpg"
    asyncio.run(cover_still(work, max(0.5, min(4.0, timeline[next(iter(timeline))][1] - 0.8)), cover))
    print("cover:", cover)
    with open(os.path.splitext(out_path)[0] + ".timeline.json", "w") as f:
        json.dump({"duration": dur, "scenes": timeline}, f, ensure_ascii=False, indent=1)
    n = 4
    step = dur / n
    parts = [os.path.join(work, f"part{i}.mp4") for i in range(n)]

    async def all_chunks():
        await asyncio.gather(*[chunk(work, i, i * step, (i + 1) * step if i < n - 1 else dur, parts[i]) for i in range(n)])
    asyncio.run(all_chunks())
    with open(os.path.join(work, "list.txt"), "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(work, "joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(work, "list.txt"), "-c", "copy", joined], check=True)
    tmp = out_path + ".tmp.mp4"
    amb = os.path.join(HERE, "audio", "calm_ambience.m4a")
    missing = [s for s in clips if s not in timeline]
    if missing:
        raise SystemExit(f"narration scenes not in the timeline: {missing}; valid: {list(timeline)}")
    if clips:
        audio_in, parts_f = [], []
        for k, (sid, (p, d)) in enumerate(clips.items()):
            audio_in += ["-i", p]
            ms = int((timeline[sid][0] + (0.05 if sid == "hook" else 0.35)) * 1000)
            parts_f.append(f"[{k + 1}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{k}]")
        mix = "".join(f"[a{k}]" for k in range(len(clips)))
        fc = ";".join(parts_f) + f";{mix}amix=inputs={len(clips)}:normalize=0,apad=whole_dur={dur:.2f}[aout]"
        afilter = ["-filter_complex", fc]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, *audio_in, *afilter,
                        "-map", "0:v", "-map", "[aout]", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "23", "-maxrate", "2M", "-bufsize", "4M",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{dur:.2f}",
                        "-movflags", "+faststart", tmp], check=True)
        os.rename(tmp, out_path)
        print(f"done: {out_path} ({dur:.1f}s, {os.path.getsize(out_path)/1e6:.1f} MB, narrated scenes: {', '.join(clips)})")
        return
    if data.get("audio", "silent") == "ambience" and os.path.exists(amb):
        audio_in = ["-stream_loop", "-1", "-i", amb]
        afilter = ["-af", f"afade=t=in:d=2,afade=t=out:st={max(dur - 3, 0):.2f}:d=3"]
    else:
        audio_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        afilter = []
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, *audio_in, *afilter,
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "23", "-maxrate", "2M", "-bufsize", "4M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest",
                    "-movflags", "+faststart", tmp], check=True)
    os.rename(tmp, out_path)
    print(f"done: {out_path} ({dur:.1f}s, {os.path.getsize(out_path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
