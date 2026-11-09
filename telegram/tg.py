#!/usr/bin/env python3
"""Helper for Claude's scheduled runs to talk to Telegram through the
GitHub Actions bridge (no bot token needed here).

  python3 telegram/tg.py queue <method> '<params json>' [--ref R] [--fallback-text T]
        Writes telegram/outbox/<time>-<n>-<ref>.json and prints its name.
        Queue several, then commit + push ONCE (the push triggers the send).
  python3 telegram/tg.py wait <job-name> [<job-name> ...] [--timeout 600]
        git pull in a loop until telegram/sent/<job-name> exists for each,
        then prints the results (ok, message_id, error) as JSON.
  python3 telegram/tg.py inbox [--since 2026-11-09T15:00:00Z]
        Prints the owner's messages saved by the bridge (newest last).

`--ref` is a free label (e.g. "news-gta6", "preview-bukhari-009") kept in the
result so you can match it.
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TG = os.path.join(ROOT, "telegram")


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


def cmd_queue(a):
    os.makedirs(os.path.join(TG, "outbox"), exist_ok=True)
    params = json.loads(a.params)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    ref = re.sub(r"[^A-Za-z0-9_-]+", "-", a.ref or a.method)[:40]
    existing = len(os.listdir(os.path.join(TG, "outbox")))
    name = f"{stamp}-{existing:03d}-{ref}.json"
    job = {"method": a.method, "params": params, "ref": a.ref}
    if a.fallback_text:
        job["fallback_text"] = a.fallback_text
    json.dump(job, open(os.path.join(TG, "outbox", name), "w"), ensure_ascii=False, indent=1)
    print(name)


def cmd_wait(a):
    deadline = time.time() + a.timeout
    pending = set(a.jobs)
    results = {}
    while pending and time.time() < deadline:
        git("pull", "--rebase", "-q")
        for j in list(pending):
            p = os.path.join(TG, "sent", j)
            if os.path.exists(p):
                results[j] = json.load(open(p))
                pending.discard(j)
        if pending:
            time.sleep(15)
    for j in pending:
        results[j] = {"ok": False, "error": "timeout: the bridge did not send it yet "
                      "(check the Actions tab / the TELEGRAM_BOT_TOKEN secret)"}
    print(json.dumps(results, ensure_ascii=False, indent=1))
    sys.exit(0 if all(r.get("ok") for r in results.values()) else 1)


def cmd_inbox(a):
    git("pull", "--rebase", "-q")
    p = os.path.join(TG, "inbox.jsonl")
    if not os.path.exists(p):
        print("[]"); return
    rows = [json.loads(l) for l in open(p) if l.strip()]
    if a.since:
        rows = [r for r in rows if r["date_utc"] >= a.since]
    print(json.dumps(rows, ensure_ascii=False, indent=1))


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
q = sub.add_parser("queue"); q.add_argument("method"); q.add_argument("params")
q.add_argument("--ref"); q.add_argument("--fallback-text")
w = sub.add_parser("wait"); w.add_argument("jobs", nargs="+"); w.add_argument("--timeout", type=int, default=600)
i = sub.add_parser("inbox"); i.add_argument("--since")
a = ap.parse_args()
{"queue": cmd_queue, "wait": cmd_wait, "inbox": cmd_inbox}[a.cmd](a)
