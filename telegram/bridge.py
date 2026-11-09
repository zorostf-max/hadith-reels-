#!/usr/bin/env python3
"""Telegram bridge run by GitHub Actions (.github/workflows/telegram.yml).

Claude never holds the bot token. Instead:
  * To SEND: commit a JSON file to telegram/outbox/ (see README.md). This
    script calls the Bot API for each file (oldest name first), writes the
    result to telegram/sent/<same name> and deletes the outbox file.
  * To READ replies: this script calls getUpdates and appends the owner's
    private messages (only from OWNER_CHAT_ID, text only) to
    telegram/inbox.jsonl. Everything else (channel posts, other users) is
    dropped, because this repository is public.

Env: TELEGRAM_BOT_TOKEN (Actions secret). The owner chat id is read from
state.json -> telegram_chat_id.
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TG = os.path.join(ROOT, "telegram")
OUTBOX, SENT = os.path.join(TG, "outbox"), os.path.join(TG, "sent")
INBOX = os.path.join(TG, "inbox.jsonl")
CURSOR = os.path.join(TG, "cursor.json")
ALLOWED = {"sendMessage", "sendPhoto", "sendVideo", "sendDocument",
           "sendMediaGroup", "editMessageText", "deleteMessage", "getChat",
           "getChatMember", "getMe"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def api(token, method, params):
    data = {k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
            for k, v in params.items() if v is not None}
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return json.load(e)
        except Exception:
            return {"ok": False, "description": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def send_outbox(token):
    os.makedirs(SENT, exist_ok=True)
    if not os.path.isdir(OUTBOX):
        return 0
    n = 0
    for name in sorted(os.listdir(OUTBOX)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(OUTBOX, name)
        try:
            job = json.load(open(path))
            method, params = job["method"], job.get("params", {})
            if method not in ALLOWED:
                res = {"ok": False, "description": f"method {method} not allowed"}
            else:
                res = api(token, method, params)
                # A photo/video Telegram cannot fetch: fall back to a text
                # message when the job asks for it.
                if not res.get("ok") and job.get("fallback_text"):
                    fb = api(token, "sendMessage", {
                        "chat_id": params.get("chat_id"),
                        "text": job["fallback_text"],
                        "parse_mode": params.get("parse_mode")})
                    res = {**fb, "fallback_used": True,
                           "first_error": res.get("description")}
        except Exception as e:
            job, res = {}, {"ok": False, "description": f"bad job file: {e}"}
        r = res.get("result")
        out = {"job": name, "ref": job.get("ref"), "method": job.get("method"),
               "ok": bool(res.get("ok")), "sent_at": now(),
               "message_id": r.get("message_id") if isinstance(r, dict) else None,
               "message_ids": [m.get("message_id") for m in r] if isinstance(r, list) else None,
               "error": None if res.get("ok") else res.get("description"),
               "fallback_used": res.get("fallback_used", False)}
        json.dump(out, open(os.path.join(SENT, name), "w"), ensure_ascii=False, indent=1)
        os.remove(path)
        n += 1
        print(f"{name}: {'ok' if out['ok'] else 'FAILED ' + str(out['error'])}")
        time.sleep(1.2)  # stay well under Telegram's per-chat rate limit
    return n


def read_inbox(token, owner):
    cur = json.load(open(CURSOR)) if os.path.exists(CURSOR) else {}
    offset = cur.get("last_update_id")
    if offset is None:
        # Carry over the cursor the old AnythingMCP flow kept in state.json.
        try:
            offset = json.load(open(os.path.join(ROOT, "state.json"))).get("telegram_last_update_id")
        except Exception:
            offset = None
    res = api(token, "getUpdates", {
        "offset": (offset + 1) if offset else None, "timeout": 0,
        "allowed_updates": ["message", "edited_message"]})
    if not res.get("ok"):
        print("getUpdates failed:", res.get("description"))
        return 0
    n, last = 0, offset
    with open(INBOX, "a") as f:
        for u in res["result"]:
            last = u["update_id"]
            m = u.get("message") or u.get("edited_message")
            if not m or str(m.get("chat", {}).get("id")) != str(owner):
                continue
            rec = {"update_id": u["update_id"], "message_id": m.get("message_id"),
                   "date_utc": datetime.fromtimestamp(m["date"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "text": m.get("text") or m.get("caption") or "",
                   "reply_to_message_id": (m.get("reply_to_message") or {}).get("message_id"),
                   "edited": "edited_message" in u}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    if last != offset:
        json.dump({"last_update_id": last, "checked_at": now()}, open(CURSOR, "w"), indent=1)
    else:
        json.dump({"last_update_id": offset, "checked_at": now()}, open(CURSOR, "w"), indent=1)
    print(f"inbox: {n} new owner message(s)")
    return n


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("::warning::TELEGRAM_BOT_TOKEN secret is not set; nothing done.")
        return
    owner = json.load(open(os.path.join(ROOT, "state.json")))["telegram_chat_id"]
    send_outbox(token)
    if "--no-inbox" not in sys.argv:
        read_inbox(token, owner)


if __name__ == "__main__":
    main()
