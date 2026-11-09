#!/usr/bin/env python3
"""Queue a hadith reel for the public Telegram channel (state.json ->
telegram_channel, e.g. @HadithDailyAr), the same video and caption as TikTok.

  python3 telegram/post_hadith.py NNN --at 2026-11-11T07:00:00Z [--video-url URL]

--at is the slot time in UTC (the bridge sends it at its first run after it).
--video-url defaults to the raw main URL; pass the commit-pinned URL when the
video was re-rendered. Telegram captions are limited to 1024 characters, so a
longer caption is split at a paragraph break: the video carries the first part
(hook question + engagement question + hadith) and a text message right after
carries the rest (explanation points, sources, hashtags).
Prints the queued job names. Commit + push afterwards.
"""
import argparse, json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = 1024


def split_caption(text):
    text = text.strip()
    if len(text) <= LIMIT:
        return text, None
    paras = text.split("\n\n")
    head = ""
    for i, p in enumerate(paras):
        cand = (head + "\n\n" + p) if head else p
        if len(cand) > LIMIT:
            break
        head = cand
    else:
        i = len(paras)
    if not head:  # first paragraph alone is too long: cut at a line break
        cut = text.rfind("\n", 0, LIMIT)
        cut = cut if cut > 200 else LIMIT
        return text[:cut].rstrip(), text[cut:].lstrip()
    return head, "\n\n".join(paras[i:]).strip()


def queue(method, params, ref, at):
    out = subprocess.run(
        ["python3", os.path.join(ROOT, "telegram", "tg.py"), "queue", method,
         json.dumps(params, ensure_ascii=False), "--ref", ref, "--not-before", at],
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


ap = argparse.ArgumentParser()
ap.add_argument("number", type=int)
ap.add_argument("--at", required=True)
ap.add_argument("--video-url")
a = ap.parse_args()
n = f"{a.number:03d}"
state = json.load(open(os.path.join(ROOT, "state.json")))
chan = state.get("telegram_channel", "@HadithDailyAr")
url = a.video_url or f"https://raw.githubusercontent.com/zorostf-max/hadith-reels-/main/videos/bukhari-{n}.mp4"
cap = open(os.path.join(ROOT, "videos", f"bukhari-{n}.txt")).read()
head, rest = split_caption(cap)
jobs = [queue("sendVideo", {"chat_id": chan, "video": url, "caption": head,
                            "supports_streaming": True}, f"channel-bukhari-{n}", a.at)]
if rest:
    # One second later in the name order, same time: sent right after the video.
    jobs.append(queue("sendMessage", {"chat_id": chan, "text": rest[:4096],
                                      "disable_web_page_preview": True},
                      f"channel-bukhari-{n}-text", a.at))
print("\n".join(jobs))
