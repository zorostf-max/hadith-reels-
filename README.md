# hadith-reels

Animated reels of Sahih al-Bukhari hadiths, in order, each with points from Shaykh Ibn Uthaymeen's explanation. Published to Instagram, YouTube (Short) and TikTok for the account 963aperture_soul, **only after the owner approves each video on Telegram**.

- `tool/template.html` + `tool/render.py`: the animation. `python3 tool/render.py data/bukhari-NNN.json videos/bukhari-NNN.mp4` renders a video; add `--check` (and an output path in a scratch folder) to write one still per scene instead.
- `data/bukhari-NNN.json`: content of each video. `videos/bukhari-NNN.mp4` + `.txt`: the video and its post caption.
- `state.json`: shared state between scheduled runs. Always pull before reading it, and commit + push after changing it.
- Public video URL used for Telegram and publishing: `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/main/videos/bukhari-NNN.mp4`

---

## RUNBOOK A — prepare a batch (runs the evening before a publishing day)

1. `git pull`. Read `state.json`. If `pending_batch` exists with status `awaiting` and its date is today or later, stop (a batch is already waiting for approval).
2. Pick 3 hadith numbers: first any numbers listed in `rejected_notes` (redo them and apply the owner's note), then continue from `next_hadith`.
3. For each hadith, research with WebSearch/WebFetch:
   - The exact text of Sahih al-Bukhari hadith N (e.g. dorar.net, sunnah.com, shamela.ws). Use the narrator chain only from the Companion onward (عن ... رضي الله عنه/عنها).
   - Ibn Uthaymeen's explanation of this hadith: his شرح صحيح البخاري, or his other works on the same hadith (شرح الأربعين النووية، شرح رياض الصالحين، فتاوى). Use only points you actually found in a source, paraphrased faithfully, never invented. If no explanation by Ibn Uthaymeen can be found for this hadith, the owner's rule is: use the verified explanation of another trusted Saudi scholar of Ahl al-Sunnah wal-Jama'ah — for example الشيخ عبد العزيز بن باز، الشيخ صالح الفوزان، الشيخ عبد المحسن العباد، الشيخ عبد الكريم الخضير، الشيخ صالح آل الشيخ، أو فتاوى اللجنة الدائمة — taken from their own books, official websites (e.g. binbaz.org.sa, alfawzan.af.org.sa, shkhudheir.com) or recorded lessons. Name that scholar accurately in the "الشرح" scene (`scholar` field), in the caption heading («من شرح الشيخ … حفظه الله / رحمه الله» as fits) and in the sources, and mention the substitution in the Telegram preview message. Never use scholars outside that description, and never attribute a point to a scholar without a source. If none of them has a findable explanation, skip the hadith and say why in the Telegram message.
4. Write `data/bukhari-NNN.json` (schema below). Matn: full text with tashkeel when available; if the hadith is very long, keep the Prophet's ﷺ words (the core statement) and say «مختصر» in the caption. Split the matn into pages of at most ~24 words. Keep each isnad/point line short (≤ ~22 characters per line, use `<br>`). 2–4 points per video. Target length 45–90 s.
5. Run `--check`, look at the stills (text must fit inside the arch, nothing cut off), fix the data if needed, then render the mp4. Keep files under 19 MB.
6. Write `videos/bukhari-NNN.txt` caption in the same shape as `videos/bukhari-001.txt`: title line, hadith text, «من شرح الشيخ ابن عثيمين رحمه الله:» numbered points, «📚 المصادر:» with exact sources (book, chapter, hadith number; the sharh book you used), then hashtags. Max 2,000 characters.
7. Commit + push the json, mp4 and txt.
8. Telegram (AnythingMCP connector, tool `telegram_bot_send_video`, chat_id from state): send each video by its raw URL with a short caption «(١/٣) الحديث رقم N — <موضوع قصير> — يُنشر <الوقت>». Then `telegram_bot_send_message` with:
   «📋 دفعة <التاريخ>: ٣ فيديوهات جاهزة للمراجعة.
   ✅ للموافقة على الكل أرسل: موافق
   ✅ لبعضها: موافق ١ ٣
   ❌ للرفض مع ملاحظة: رفض ٢ <ملاحظتك>
   لن يُنشر شيء قبل موافقتك.»
9. Set `pending_batch` = `{"publish_date": "<tomorrow YYYY-MM-DD>", "hadiths": [n1,n2,n3], "status": "awaiting", "approved": [], "rejected": [], "scheduled": {}}`, advance `next_hadith` past the new numbers (not past redone ones), clear `rejected_notes` entries you redid. Commit + push.

## RUNBOOK B — check approval and schedule (runs on publishing days at ~07:25, 12:25, 19:25)

1. `git pull`. Read `state.json`. If there is no `pending_batch`, or its status is `done`, stop quietly.
2. Read new Telegram messages with `telegram_bot_get_updates` (this consumes them). Keep only messages from the owner's chat_id sent after the batch previews. Save the raw text of any you read into `pending_batch.messages` so later runs still see them.
3. Interpret the owner's replies (Arabic, free wording is fine): «موافق» alone = all approved; «موافق ١ ٣» = those positions; «رفض ٢ …» = rejected with a note. Numbers refer to positions 1–3 in the batch. If the meaning is unclear, ask on Telegram and stop.
4. For each approved, not-yet-scheduled video, in order, take the next slot of `publish_date` (08:00, 13:00, 20:00 Europe/Istanbul) that is still at least 10 minutes away; if none is left today, use the next day's slots. Schedule it with Metricool `createScheduledPost`, blogId from state, ONE post with providers instagram + youtube + tiktok:
   - media: the raw GitHub URL; text: the caption file content
   - instagramData `{"type":"REEL"}`
   - youtubeData `{"title": "<موضوع الحديث> | الحديث رقم N من صحيح البخاري – شرح ابن عثيمين" (≤100 chars), "type":"short", "privacy":"public", "category":"EDUCATION", "madeForKids": false, "tags": [...]}`
   - tiktokData `{"title": "<same title, shorter>", "privacyOption":"PUBLIC_TO_EVERYONE", "autoAddMusic": false, "disableComment": false, "disableDuet": false, "disableStitch": false}`
   Record the slot and plannerUrl in `pending_batch.scheduled`, and add the number to `published`.
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
  "scholar_dua": "optional; defaults to رحمه الله — use حفظه الله for a living scholar"
}
```
`gold_words`: `[page, firstWord, endWord)` ranges coloured gold. Write «صلى الله عليه وسلم» in full (the font has no ﷺ glyph). Only the Arabic font DejaVu Sans is available.
