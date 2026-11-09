# Telegram bridge (GitHub Actions)

Replaces the AnythingMCP "Telegram Bot API" connector. The bot (`@my_cs2_monitor_bot`) token is stored only as the repository secret `TELEGRAM_BOT_TOKEN`; the workflow `.github/workflows/telegram.yml` runs `bridge.py`.

- **Send:** queue one JSON job per message in `telegram/outbox/`, then commit + push once. The push starts the workflow, which sends the jobs (oldest first), writes each result to `telegram/sent/<job>` (`ok`, `message_id`, `error`) and removes the job. Sending takes about 1 minute.
- **Read replies:** every 15 minutes (and after every send) the workflow saves the owner's new private messages to `telegram/inbox.jsonl` (`date_utc`, `message_id`, `text`, `reply_to_message_id`). Only messages from `state.json → telegram_chat_id` are kept, text only, because the repo is public. To force a fresh read, queue a `getMe` job and push.
- **Never** try to call the Telegram API directly from a session (there is no token here) and never use AnythingMCP's Telegram tools any more.

## How to use it from a run

```bash
git pull --rebase -q
# queue (params are the Bot API method's parameters)
J1=$(python3 telegram/tg.py queue sendPhoto '{"chat_id":"@LevelUpGames0","photo":"https://…jpg","caption":"…","parse_mode":"HTML"}' --ref news-gta6 --fallback-text "…same text…")
J2=$(python3 telegram/tg.py queue sendVideo '{"chat_id":"6875821347","video":"https://raw.githubusercontent.com/…/bukhari-009.mp4","caption":"…"}' --ref preview-009)
git add telegram/outbox && git commit -qm "telegram: queue 2" && git push -q   # (pull --rebase and retry if rejected)
python3 telegram/tg.py wait "$J1" "$J2"        # prints ok / message_id / error for each
python3 telegram/tg.py inbox --since 2026-11-09T15:00:00Z   # owner's replies
```

Supported methods: sendMessage, sendPhoto, sendVideo, sendDocument, sendMediaGroup, editMessageText, deleteMessage, getChat, getChatMember, getChatAdministrators (only bots are kept), getMe. Add `--not-before <UTC>` to hold a job until a time (checked every 15 min). `telegram/post_hadith.py` queues a hadith reel for the public channel. Media must be public HTTPS URLs (photo ≤ 5 MB, video ≤ 20 MB by URL). `--fallback-text` sends that text as a plain message if the media is refused.

If `wait` times out: the secret is missing/wrong or Actions is disabled. Report it in the run summary; do not retry in a loop.
