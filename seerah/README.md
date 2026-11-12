# Seerah series — runbooks for the scheduled runs

Owner's series «السيرة النبوية»: a father tells the Prophet's ﷺ biography to his children مريم and عمر. Still illustrations (warm soft flat storybook style, faceless figures, no facial features), slow camera moves, speech bubbles / captions, Arabic voices. No music, ever. Everything the owner sees is in Arabic; his reply words are English (`ok` / `no <note>`).

**Schedule (owner's decision 2026-11-10/12):** one episode on **Tuesday and Thursday at 10:00 Europe/Istanbul** (`state.json → seerah.days`, `seerah.slot`). Mon/Wed/Fri belong to the hadith videos; nothing at the weekend.

**Pipeline — 3 scheduled runs, every step needs the owner's approval:**

| Run | When (Istanbul) | Does |
|---|---|---|
| S1 script | Tue + Thu ~19:47 | writes the script of the next episode and sends it for review |
| S2 production | Mon + Wed ~19:13 | if the script is approved: images, voices, render, caption, sends the preview video |
| S3 approval | Tue + Thu ~09:23 | if the video is approved: schedules it for 10:00 the same day |
| C1 compilation | Fri ~19:37 | joins the week's Tuesday + Thursday episodes into one video and sends it for approval |
| C2 compilation approval | Sat ~09:27 | if approved: schedules it on **YouTube only** (normal video, not a Short) at 10:00 |

Thursday's S1 prepares Tuesday's episode; Tuesday's S1 prepares Thursday's.

`state.json → seerah.pending` holds the episode in progress:
`{"episode": N, "publish_date": "YYYY-MM-DD", "status": "script_sent" | "script_approved" | "video_sent" | "scheduled" | "skipped", "script_message_ids": [], "preview_message_ids": [], "notes": [], "messages": []}`.

Telegram goes ONLY through the GitHub bridge (`telegram/README.md`): queue jobs with `telegram/tg.py`, commit + push once, `tg.py wait`. Before reading replies, refresh: queue `getMe` (`--ref inbox-refresh`), push, wait, then `tg.py inbox`. Never AnythingMCP, never getUpdates. Owner chat: `state.json → telegram_chat_id`.

---

## S1 — write the next script

1. `git pull`. Read `state.json → seerah`. The target date = the next Tuesday or Thursday after today. If `pending` exists for that date with status other than `skipped`, stop. If `pending` is for an earlier date and was never scheduled, re-use its episode number (carry it over; the old script may be re-sent with any notes applied).
2. Episode N = `seerah.next_episode` (or the carried-over one); topic = `seerah.next_topic`, then continue in the order of **الرحيق المختوم** (صفي الرحمن المباركفوري). Research with WebSearch/WebFetch in trusted sources only: الرحيق المختوم first; for details also سيرة ابن هشام، زاد المعاد، البداية والنهاية، الفصول في السيرة لابن كثير، and authentic hadith (Bukhari/Muslim). Never invent events, words, names, numbers or dates; where the books differ, say «في أشهر الأقوال» or keep to the agreed point. Weak or fabricated stories are left out.
3. Write `seerah/epNN/script.json` with the same schema as `seerah/ep01/script.json` (copy `voices`, `tts_model`, the `majlis` image entry): full account in a storytelling style, scenes that alternate the majlis (children asking — sometimes مريم, sometimes عمر — and the father answering) with story illustrations; `tts` with tashkeel on names and key words, «صلّى الله عليه وسلّم» in full; short `bubble` / `caption` lines. Opening = a child's gripping question (the hook). **Closing line rule:** the last father line names the next episode's day — an episode aired on Tuesday ends «هذه حكايةُ يومِ الخميسِ إن شاءَ الله», one aired on Thursday ends «هذه حكايةُ يومِ الثلاثاءِ إن شاءَ الله». Add `sources` (book + chapter). Image `prompt`s must follow ep01's style text (vertical 9:16, warm soft flat storybook, faceless distant figures, no text). **Never depict the Prophet ﷺ, any prophet, the Companions' faces, or angels** — show places, objects, light, landscapes, distant faceless crowds instead.
   **Length:** spoken text for a finished video of 2:00–2:50 (YouTube Shorts allow at most 3:00); ep01 = 2:59 was the upper edge.
4. Commit + push. Send the script to the owner for review: one `sendMessage` job (split into several messages if over 3,500 characters) with the title, then each scene as «🖼 <المشهد>» + the spoken lines prefixed «👨 الأب: / 👧 مريم: / 👦 عمر:», then «📚 المصادر», then:
   «📝 سكربت الحلقة N (<العنوان>) — تُنشر <اليوم والتاريخ> الساعة ١٠:٠٠.
   ✅ للموافقة أرسل: ok
   ✏️ للتعديل: no <ملاحظتك>
   سيُصنع الفيديو بعد موافقتك فقط.»
   Push, `tg.py wait`, store message_ids.
5. Set `pending` = `{"episode": N, "publish_date": "<target date>", "status": "script_sent", "script_message_ids": [...], ...}`. Commit + push.

## S2 — produce the video (only if the script is approved)

1. `git pull`. Read `seerah.pending`. If it is missing, or its `publish_date` is not the next day, or status is not `script_sent`/`script_approved`, stop quietly.
2. Refresh the inbox and read the owner's replies sent after `script_message_ids[0]`; save their text in `pending.messages`.
   - `ok` / `yes` / `موافق` → approved.
   - `no <note>` / an edit request → apply the notes to `script.json`, re-send the changed script as in S1 step 4 (ask for `ok` again), keep status `script_sent`, and stop — the video is made at the next S2 run only if approved by then; otherwise the episode moves (see 6).
   - No reply → send «⏰ تذكير: سكربت الحلقة N ينتظر موافقتك؛ لن تُنشر غدًا ما لم توافق.» and stop.
3. **Images:** for each image with a `prompt` and no file yet, generate it with ElevenLabs `creative_generate_image` (one flow per episode via `creative_create_flow`, named «seerah-epNN»; portrait 9:16; one variation is enough), download with `curl -sSfL -o seerah/epNN/img/<name>.png "<content_url>"`, and look at each picture: reject anything with a visible face, a depiction of a prophet/angel, text, letters, crosses in close-up or a style far from ep01 — regenerate that one once with a corrected prompt. Re-use existing pictures (`seerah/assets/majlis.png`, and ep01's images when the place matches) instead of generating new ones.
4. **Voices:** ElevenLabs `creative_generate_speech`, `model_id` = `tts_model`, the voice_id of each speaker from `voices` (father `YKGG8oefXIWbncG7wgoX`, مريم `NQyF5U0t336unYhQXcuv`, عمر `0pDT8WvJXiBq0hxYB2Cp`), **`generations_count: 1`**, all clips on the episode's flow. Never call generate twice to retry. Save as `seerah/epNN/audio/sNN[a-d].mp3` in script order (letters for several lines in one scene, as in ep01). If ElevenLabs refuses (credits, busy) or the download is blocked, stop and tell the owner on Telegram why — do not publish a silent episode.
5. Render: `python3 seerah/render_episode.py seerah/epNN --check`, look at every still (bubbles inside the frame, nothing cut off, Arabic shaped correctly), fix, then `python3 seerah/render_episode.py seerah/epNN`. Must be ≤ 2:58 and < 19 MB; if longer, shorten lines, regenerate only changed clips, render again.
6. Write `seerah/epNN/caption.txt` like ep01's: line 1 = hook question + « 🤔», line 2 = «💬 » + engagement question, blank, «السيرة النبوية · الحلقة N: <العنوان>», a 2–4 sentence summary, «👨‍👧‍👦 يحكيها الأب لابنه عمر وابنته مريم», «📅 حلقة جديدة كل ثلاثاء وخميس، والحلقة القادمة يوم <اليوم> إن شاء الله», «📚 المصادر:» (owner's rule: sources in the description, not in the video), a short like/share call to action, 4–5 hashtags. Max 2,000 characters.
7. Commit + push. Send the preview: `sendVideo` with the commit-pinned raw URL `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/<sha>/seerah/epNN/episode.mp4` and caption «🎬 الحلقة N — <العنوان> — تُنشر <اليوم> ١٠:٠٠», then a `sendMessage`:
   «✅ للموافقة على النشر أرسل: ok
   ❌ للرفض مع ملاحظة: no <ملاحظتك>
   ⏰ تُفحص موافقتك مرة واحدة الساعة ٩:٢٥ صباح يوم النشر، فأرسل ردّك قبلها.
   لن يُنشر شيء قبل موافقتك.»
   Push, wait, store `preview_message_ids`, status `video_sent`. Commit + push.
8. If the episode cannot be finished for its date, set status `skipped` with the reason; the next S1 carries it over to the next Tuesday/Thursday (fix the closing line's day if it changes).

## S3 — check approval and schedule

1. `git pull`. If `seerah.pending` is missing, its `publish_date` is not today, or status is not `video_sent`, stop quietly.
2. Refresh the inbox; read replies after `preview_message_ids[0]`; save them in `pending.messages`.
3. `ok` / `yes` / `موافق` → schedule with Metricool `createScheduledPost` (blogId `state.json → metricool_blog_id`), ONE post, providers instagram + youtube + tiktok, at **today 10:00 Europe/Istanbul**:
   - media: the commit-pinned raw URL of `episode.mp4`; text: `caption.txt` as-is
   - instagramData `{"type":"REEL","showReelOnFeed":true}`
   - youtubeData `{"title":"السيرة النبوية | الحلقة N: <العنوان> – <وصف قصير>" (≤100 chars),"type":"short","privacy":"public","category":"EDUCATION","madeForKids":false,"tags":[...]}`
   - tiktokData `{"title":"السيرة النبوية · الحلقة N: <العنوان>","privacyOption":"PUBLIC_TO_EVERYONE","autoAddMusic":false}`
   Then queue the same video + caption for the Telegram channel `state.json → telegram_channel`: `tg.py queue sendVideo '{"chat_id":"@HadithDailyAr","video":"<url>","caption":"<caption>","supports_streaming":true}' --ref seerah-epNN --not-before <today>T06:55:00Z` (if the caption is over 1024 characters, put the first part in the video caption and queue the rest as a `sendMessage` with the same `--not-before`). Commit + push.
   Record in `seerah.epNN` (`publish_at`, `metricool_post_id`, `telegram_job`, `approved`), set status `scheduled`, `next_episode` = N+1, `next_topic` = the topic that follows in الرحيق المختوم, and send the owner «✅ جُدولت الحلقة N لليوم الساعة ١٠:٠٠ على إنستغرام ويوتيوب وتيك توك وقناة تيليغرام.».
4. `no <note>` → status `skipped`, keep the note in `pending.notes` (the next S1 redoes the episode with it); tell the owner it will move to the next slot.
5. No reply → nothing is published; status `skipped` (reason: no approval); tell the owner the episode moves to the next Tuesday/Thursday.
6. Never publish an episode the owner did not approve. Never change posts already scheduled unless the owner asks.

---

## Saturday compilation (owner's decision 2026-11-12): the week's two episodes in one video, on YouTube only

`state.json → seerah.compilation` = `{"week_of": "YYYY-MM-DD (Saturday)", "episodes": [N1, N2], "status": "sent" | "scheduled" | "skipped", "preview_message_ids": [], "messages": []}`.

### C1 — build (Friday)
1. `git pull`. Find the episodes of this week whose `seerah.epNN.publish_at` is this Tuesday and this Thursday (they must have been scheduled/published). If fewer than 2, stop quietly (no compilation this week).
2. Join them with ffmpeg into `seerah/compilations/<saturday-date>.mp4` (1080x1920, H.264 `-preset veryfast -crf 23`, AAC; re-encode with the concat filter so audio stays in sync; a 0.5 s fade between the two). No music.
3. Write `seerah/compilations/<saturday-date>.txt` (YouTube description): first line «السيرة النبوية · الحلقتان N1 و N2: <العنوان١> و<العنوان٢>», a short summary of each, «📅 حلقة جديدة كل ثلاثاء وخميس، ومجموع الأسبوع كل سبت», the combined «📚 المصادر:» of both episodes, a like/subscribe call to action, 4–5 hashtags.
4. Commit + push. Telegram (bridge): the file is over Telegram's 20 MB URL limit, so send a `sendMessage` with the commit-pinned raw link and:
   «🎞 مجموع الأسبوع (الحلقتان N1 و N2) جاهز للمراجعة — يُنشر على يوتيوب فقط السبت ١٠:٠٠.
   <الرابط>
   ✅ للموافقة أرسل: ok
   ❌ للرفض: no <ملاحظتك>
   ⏰ تُفحص موافقتك الساعة ٩:٢٥ صباح السبت.»
   Push, wait, store message_ids; set `seerah.compilation` with status `sent`. Commit + push.

### C2 — approve and schedule (Saturday)
1. `git pull`. If `seerah.compilation.week_of` is not today or status is not `sent`, stop quietly.
2. Refresh the inbox, read replies after `preview_message_ids[0]`, save them.
3. `ok` → Metricool `createScheduledPost`, providers **youtube only**, today 10:00 Europe/Istanbul, media = commit-pinned raw URL, text = the .txt, youtubeData `{"title":"السيرة النبوية | الحلقتان N1 و N2: <العنوان١> و<العنوان٢>" (≤100 chars),"type":"video","privacy":"public","category":"EDUCATION","madeForKids":false,"tags":[...]}`. Not on Instagram, TikTok or Telegram. Status `scheduled`, record the plannerUrl, tell the owner.
4. `no` or no reply → nothing is published; status `skipped`; tell the owner.
