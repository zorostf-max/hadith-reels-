"""Render a hadith reel from a data JSON file.

Usage:  python3 render.py path/to/data.json path/to/output.mp4
The data file follows the schema in README.md. Output: 1080x1920, 30 fps,
H.264 + AAC (calm ambience bed from tool/audio by default; "audio": "silent" in the data file turns it off), kept under ~18 MB so Telegram can fetch it by URL.
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
        await b.close()
        return d


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


def main():
    data_path, out_path = sys.argv[1], os.path.abspath(sys.argv[2])
    check_only = "--check" in sys.argv
    work = tempfile.mkdtemp(prefix="reel_")
    shutil.copy(os.path.join(HERE, "template.html"), os.path.join(work, "index.html"))
    data = json.load(open(data_path, encoding="utf-8"))
    with open(os.path.join(work, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA=" + json.dumps(data, ensure_ascii=False) + ";")
    if check_only:
        outdir = os.path.dirname(out_path)
        asyncio.run(stills(work, None, outdir))
        print("stills written to", outdir)
        return
    dur = asyncio.run(duration(work))
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
