# hadith-reels

Animated reels of Sahih al-Bukhari hadiths, in order, each with points from Shaykh Ibn Uthaymeen's explanation. Published to Instagram, YouTube (Short) and TikTok for the account 963aperture_soul, **only after the owner approves each video on Telegram**.

- `tool/template.html` + `tool/render.py`: the animation. `python3 tool/render.py data/bukhari-NNN.json videos/bukhari-NNN.mp4` renders a video; add `--check` (and an output path in a scratch folder) to write one still per scene instead. `--theme morning|noon|night` overrides the data file's theme.
- `data/bukhari-NNN.json`: content of each video. `videos/bukhari-NNN.mp4` + `.txt`: the video and its post caption.
- **Background follows the publishing time** (owner's request): `morning` = 10:00 slot (dawn sky, sun rising behind the dome), `noon` (blue midday sky, sun high — not used while there are only 2 daily slots), `night` = 18:00 slot (night sky, crescent moon, lit lanterns). The mapping is in `state.json` → `slot_themes`.
- `state.json`: shared state between scheduled runs. Always pull before reading it, and commit + push after changing it.
- Public video URL used for Telegram and publishing: `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/main/videos/bukhari-NNN.mp4`

---

## RUNBOOK A — prepare a batch (runs on each publishing day at ~17:20, so the previews reach the owner around the time the day's last video goes out at 18:00; the batch is for the next publishing day, two days later)

1. `git pull`. Read `state.json`. If `pending_batch` exists with status `awaiting` and its `publish_date` is later than today, stop (a batch is already waiting for approval). If it is still `awaiting` (or partly unanswered) and its `publish_date` is today or earlier, the owner did not reply before the single morning check: its unapproved, unrejected hadiths were NOT published, so put them first in the new batch (their data/videos already exist; re-render only if the theme for the new slot differs) and do not count them as published.
2. Pick **2** hadith numbers — after any carried-over ones from step 1 — (owner's request since 2026-11-07: 2 videos per publishing day, at 10:00 and 18:00 — the best times on TikTok, YouTube and Instagram per Metricool): first any numbers listed in `rejected_notes` (redo them and apply the owner's note), then continue from `next_hadith`.
3. For each hadith, research with WebSearch/WebFetch:
   - The exact text of Sahih al-Bukhari hadith N (e.g. dorar.net, sunnah.com, shamela.ws). Use the narrator chain only from the Companion onward (عن ... رضي الله عنه/عنها).
   - Ibn Uthaymeen's explanation of this hadith: his شرح صحيح البخاري, or his other works on the same hadith (شرح الأربعين النووية، شرح رياض الصالحين، فتاوى). Use only points you actually found in a source, paraphrased faithfully, never invented. If no explanation by Ibn Uthaymeen can be found for this hadith, the owner's rule is: use the verified explanation of another trusted Saudi scholar of Ahl al-Sunnah wal-Jama'ah — for example الشيخ عبد العزيز بن باز، الشيخ صالح الفوزان، الشيخ عبد المحسن العباد، الشيخ عبد الكريم الخضير، الشيخ صالح آل الشيخ، أو فتاوى اللجنة الدائمة — taken from their own books, official websites (e.g. binbaz.org.sa, alfawzan.af.org.sa, shkhudheir.com) or recorded lessons. Name that scholar accurately in the "الشرح" scene (`scholar` field), in the caption heading («من شرح الشيخ … حفظه الله / رحمه الله» as fits) and in the sources, and mention the substitution in the Telegram preview message. Never use scholars outside that description, and never attribute a point to a scholar without a source. If none of them has a findable explanation, skip the hadith and say why in the Telegram message.
4. Write `data/bukhari-NNN.json` (schema below). Matn: full text with tashkeel when available; if the hadith is very long, keep the Prophet's ﷺ words (the core statement) and say «مختصر» in the caption. Set `"theme"` from the slot each video is planned for: position 1 → `morning` (10:00), 2 → `night` (18:00). Split the matn into pages of at most ~24 words. Keep each isnad/point line short (≤ ~22 characters per line, use `<br>`).
   **Short format (owner's decision 2026-11-07, after the first analytics: only 22% of Instagram viewers passed 3 s and the average watch was 5 s of a 64 s video):**
   - **Exactly 1 point** in `points` — the single most striking, practical benefit from the explanation (the rest may go in the caption).
   - **Target 30–45 s, hard maximum 55 s.** Prefer 1 matn page; if the hadith is long, keep only the Prophet's words (صلى الله عليه وسلم) on one or two pages and write «مختصر» in the caption.
   - Use 1 isnad line (the Companion only).
   - Speed up the fixed scenes with `"durations": {"intro": 2.5, "isnad": 3, "sharh": 2.2, "outro": 6.5}`. The hook stays first (3.4 s), so the question is on screen from the very first second.
   - After rendering, read the duration that render.py prints; if it is over 55 s, shorten the matn or the point and render again.
   **Hook and closing question (owner's rule, every video):** set `"hook"` — a short, gripping question drawn faithfully from the hadith itself, shown as the very first scene to stop the scroll (e.g. «ماذا رأى النبي<br><span class="gold">صلى الله عليه وسلم</span><br>بين السماء والأرض<br>فرجع يقول: زمّلوني؟»; ≤ ~4 short lines, no claim beyond the hadith text) — and `"question"` — an engagement question shown on the outro (e.g. «ما أكثر ما لفت نظرك<br>في هذا الحديث؟ اكتبه في التعليقات»; vary it per video).
5. Run `--check`, look at the stills (text must fit inside the arch, nothing cut off, the background matches its theme), fix the data if needed, then render the mp4. Keep files under 19 MB.
6. Write `videos/bukhari-NNN.txt` caption (one text goes to all three platforms, and TikTok/Reels show only the first lines, so those lines must carry the post): **first line = the hook question + « 🤔»** (same wording as `hook`, without HTML), **second line = «💬 » + the closing question**, blank line, title line, hadith text, «من شرح الشيخ ابن عثيمين رحمه الله:» numbered points (the video shows one; the caption may list up to 3), then «📚 المصادر:» with exact sources (book, chapter, hadith number; the sharh book you used), then hashtags. Max 2,000 characters.
7. Commit + push the json, mp4 and txt.
8. Telegram (AnythingMCP connector, tool `telegram_bot_send_video`, chat_id from state): send each video by its raw URL with a short caption «(١/٢) الحديث رقم N — <موضوع قصير> — يُنشر <الوقت>». Then `telegram_bot_send_message` with:
   «📋 دفعة <التاريخ>: فيديوهان جاهزة للمراجعة.
   ✅ للموافقة على الكل أرسل: ok
   ✅ لأحدهما: ok 1
   ❌ للرفض مع ملاحظة: no 2 <ملاحظتك>
   ⏰ تُفحص موافقتك مرة واحدة الساعة ٩:٢٥ صباح يوم النشر (<التاريخ>)، فأرسل ردّك قبلها.
   لن يُنشر شيء قبل موافقتك.»
9. Set `pending_batch` = `{"publish_date": "<the next publishing day = today + 2 days, YYYY-MM-DD>", "hadiths": [n1,n2], "status": "awaiting", "approved": [], "rejected": [], "scheduled": {}}`, advance `next_hadith` past the new numbers (not past redone ones), clear `rejected_notes` entries you redid. Commit + push.

## RUNBOOK B — check approval and schedule (runs ONCE on each publishing day at ~09:25 — owner's request: a single approval check)

1. `git pull`. Read `state.json`. If there is no `pending_batch`, or its status is `done`, stop quietly.
2. Read new Telegram messages with `telegram_bot_get_updates` (this consumes them). Keep only messages from the owner's chat_id sent after the batch previews. Save the raw text of any you read into `pending_batch.messages` so later runs still see them.
3. Interpret the owner's replies. The owner's chosen reply words are English: `ok` / `yes` / `approve` alone = all approved; `ok 1` = that position; `no 2 <note>` / `reject 2 <note>` = rejected with a note (the note may be in Arabic). Also accept the Arabic equivalents (موافق، رفض) and Arabic or Western digits, case-insensitive. Numbers refer to positions 1–2 in the batch. If the meaning is unclear, ask on Telegram and stop.
4. For each approved, not-yet-scheduled video, in order, take the next slot of `publish_date` (the `slots` in state.json: 10:00, 18:00 Europe/Istanbul) that is still at least 10 minutes away; if none is left today, use the next day's slots. Schedule it with Metricool `createScheduledPost`, blogId from state, ONE post with providers instagram + youtube + tiktok:
   - media: the raw GitHub URL; text: the caption file content
   - instagramData `{"type":"REEL"}`
   - youtubeData `{"title": "الحديث N | <موضوع الحديث> – صحيح البخاري" (number first so the series is easy to follow; Arabic-Indic or Western digits; ≤100 chars), "type":"short", "privacy":"public", "category":"EDUCATION", "madeForKids": false, "tags": [...]}`
   - tiktokData `{"title": "<same title, shorter>", "privacyOption":"PUBLIC_TO_EVERYONE", "autoAddMusic": false, "disableComment": false, "disableDuet": false, "disableStitch": false}`
   **Before scheduling, match the background to the slot:** the slot's theme is `slot_themes[<HH:MM>]` in state.json. If the video's data file has a different `theme` (e.g. the owner approved late, or only some videos, so a video moved to another slot), set `theme` in `data/bukhari-NNN.json`, re-render `videos/bukhari-NNN.mp4`, commit + push, and use the commit-pinned URL `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/<commit-sha>/videos/bukhari-NNN.mp4` as the media (the `main` URL is cached for minutes and could serve the old file). If re-rendering would push past the slot's 10-minute margin, take the next slot of the same theme instead. Mention any background change in the Telegram summary.
   Record the slot, theme and plannerUrl in `pending_batch.scheduled`, and add the number to `published`.
5. Rejected videos: put `{N: "<note>"}` into `rejected_notes` so the next batch redoes them; do not publish them.
6. Send one Telegram message summarising what was scheduled (times) and what was rejected. When every video in the batch is scheduled or rejected, set status `done`. Commit + push.
7. Never publish a video the owner did not approve. Never change already scheduled posts unless the owner asks.

## Data schema (`data/bukhari-NNN.json`)

```json
{
  "number": 2,
  "title": "الحديث الثاني",
  "subtitle": "من صحيح الإمام البخاري",
  "header": "صحيح البخاري · كتاب بدء الوحي · ح (٢)",
  "isnad": ["عن أم المؤمنين<br><span class=\"gold\">عائشة</span> رضي الله عنها", "…"],
  "matn_pages": ["page 1 words …", "page 2 words …"],
  "gold_words": [[0, 0, 6]],
  "points": [{"title": "…", "body": "line<br><span class=\"hl\">highlight</span>"}],
  "outro_big": "short takeaway",
  "outro_mid": "one more line",
  "scholar": "optional, HTML; defaults to الشيخ محمد بن صالح<br>العثيمين",
  "scholar_dua": "optional; defaults to رحمه الله — use حفظه الله for a living scholar",
  "theme": "morning | noon | night — background by publishing time (10:00 / 18:00; noon unused); default night",
  "hook": "opening question scene (required by the owner)",
  "question": "engagement question on the outro (required by the owner)",
  "audio": "optional; leave out (silent). The owner rejected the synthetic ambience bed, so do not set \"ambience\""
}
```
`gold_words`: `[page, firstWord, endWord)` ranges coloured gold. Write «صلى الله عليه وسلم» in full (the font has no ﷺ glyph). Only the Arabic font DejaVu Sans is available. Owner's rule: no music, ever, and never TikTok's auto-added music. Videos are silent (the owner rejected the synthetic ambience in tool/audio).
