#!/usr/bin/env python3
"""Collect fresh gaming news for the Telegram channel @LevelUpGames0.

Reads the RSS feeds below, keeps items published in the last --hours hours
that are not already in posted.txt, and prints them as JSON (newest last),
each with title, link, source, published time (UTC), summary and an image URL
taken from the feed (or the article's og:image when the feed has none).

Usage: python3 gaming-news/fetch_news.py [--hours 3] [--limit 15]
"""
import argparse, calendar, html, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

import feedparser

FEEDS = {
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
    "VGC": "https://www.videogameschronicle.com/feed/",
    "GamesRadar+": "https://www.gamesradar.com/feeds.xml",
    "IGN": "https://feeds.feedburner.com/ign/news",
    "Eurogamer": "https://www.eurogamer.net/feed",
    "Dexerto": "https://www.dexerto.com/feed/",
    "HLTV": "https://www.hltv.org/rss/news",
    "Tom's Hardware": "https://www.tomshardware.com/feeds.xml",
}
HERE = os.path.dirname(os.path.abspath(__file__))
POSTED = os.path.join(HERE, "posted.txt")
UA = "Mozilla/5.0 (compatible; LevelUpNewsBot/1.0)"


def norm(url):
    return url.split("?")[0].split("#")[0].rstrip("/").lower()


def entry_image(e):
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key, []) or []:
            if m.get("url"):
                return m["url"]
    for l in e.get("links", []):
        if l.get("rel") == "enclosure" and l.get("type", "").startswith("image"):
            return l.get("href")
    m = re.search(r'<img[^>]+src="([^"]+)"', e.get("summary", "") + str(e.get("content", "")))
    return m.group(1) if m else None


def og_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        page = urllib.request.urlopen(req, timeout=15).read(400000).decode("utf-8", "ignore")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page)
        return html.unescape(m.group(1)) if m else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=3)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--include-posted", action="store_true",
                    help="keep links already in posted.txt (the tweet task uses it to get their images)")
    a = ap.parse_args()
    posted = set()
    if os.path.exists(POSTED) and not a.include_posted:
        posted = {norm(l.split("\t")[-1]) for l in open(POSTED) if l.strip()}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=a.hours)
    items, errors = [], []
    for src, url in FEEDS.items():
        try:
            f = feedparser.parse(url, agent=UA)
            if not f.entries:
                errors.append(f"{src}: no entries")
            for e in f.entries:
                t = e.get("published_parsed") or e.get("updated_parsed")
                if not t:
                    continue
                pub = datetime.fromtimestamp(calendar.timegm(t), timezone.utc)
                link = e.get("link", "")
                if pub < cutoff or not link or norm(link) in posted:
                    continue
                summ = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "")))
                items.append({
                    "source": src, "title": html.unescape(e.get("title", "")).strip(),
                    "link": link, "published_utc": pub.strftime("%Y-%m-%d %H:%M"),
                    "summary": re.sub(r"\s+", " ", summ).strip()[:600],
                    "image": entry_image(e),
                })
        except Exception as ex:
            errors.append(f"{src}: {ex}")
    items.sort(key=lambda x: x["published_utc"])
    items = items[-a.limit:]
    for it in items:
        img = it["image"]
        # WordPress feeds give tiny thumbnails (?w=300): drop the resize params
        if img and re.search(r"[?&](w|resize|fit)=", img):
            img = img.split("?")[0]
        it["image"] = img or og_image(it["link"])
    print(json.dumps({"items": items, "feed_errors": errors}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
