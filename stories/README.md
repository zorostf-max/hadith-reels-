# «قصص من صحيح البخاري» — runbooks for the scheduled runs

Owner's new series (decided 2026-11-13, after comparing the channel with the top Arabic Islamic channels: the narrated *story* hadiths of Sahih al-Bukhari reach millions of views, while plain hadith + explanation videos stay in the hundreds; the seerah episode in this style was the channel's best video). It runs **next to** the hadith series (Mon/Wed/Fri) and the seerah series (Tue/Thu); it replaces neither.

Each episode tells ONE story that the Prophet ﷺ told or that is narrated in **Sahih al-Bukhari**, as a narrated short film: still illustrations in the seerah style (warm soft flat storybook, faceless figures), slow camera moves, one narrator voice, short on-screen captions. No music, ever. Everything the owner sees is in Arabic; his reply words are English (`ok` / `no <note>`).

**Schedule (owner's decision 2026-11-19 — replaces Saturday + Sunday 11:00):** ONE story per week, all on **Saturday** (Sunday now belongs to the seerah compilation):

| Saturday (Istanbul) | What | Where |
|---|---|---|
| 11:00 | **Part 1** (`stNN/episode.mp4`, ~1:30–2:30) | Instagram Reel + YouTube Short + TikTok + Threads + Telegram @HadithDailyAr (+ Facebook Story) |
| 11:00 | **Full story** (`stNN/full.mp4` = Part 1 + Part 2 joined, ~3–4 min) | **Facebook only, as a normal video POST** (`facebookData {"type":"POST"}` — the Reels API only accepts ≤ 90 s) |
| 18:00 | **Part 2** (`stNNb/episode.mp4`) | same as Part 1 (+ Facebook Story) |
| 20:00 | **Long video** (`stNN/long.mp4`, **8–10 min**: the full story, then «فوائد القصة» from فتح الباري / trusted scholars) | **YouTube only, normal video** (type "video", not a Short) |

So every story is written as **two parts** (even a short one: split at the moment of highest tension). `state.json → stories.days` = `["Sat"]`, `slots` = `{"part1": "11:00", "part2": "18:00", "facebook_full": "11:00", "youtube_long": "20:00"}`.
**Follow plan** (root `README.md`): the spoken follow line, the follow button (automatic in `render_episode.py`) and caption line 2 «📌 تابِعنا: قصة جديدة كل سبت» apply to every story video.

**Pipeline — 3 scheduled runs, every step needs the owner's approval** (same rules as the seerah series):

| Run | When (Istanbul) | Does |
|---|---|---|
| T1 script | **Thu** ~20:17 | writes Part 1 + Part 2 + the «فوائد» section of Saturday's story and sends them for review (one `ok` approves all) |
| T2 production | **Fri** ~19:53 | if the script is approved: images, voice, renders the 4 videos (Part 1, Part 2, full, long), captions, sends the previews |
| T3 approval | **Fri** ~23:23 (the evening before) | if the videos are approved: schedules all four for Saturday (11:00, 11:00, 18:00, 20:00) |

`state.json → stories` = `{"days": ["Sat"], "slots": {...}, "next_story": 1, "pending": {...} | null, "published": {}}`; `pending` = `{"story": N, "publish_date": "YYYY-MM-DD", "status": "script_sent" | "video_sent" | "scheduled" | "skipped", "script_message_ids": [], "preview_message_ids": [], "notes": [], "messages": []}`.

Telegram goes ONLY through the GitHub bridge (`telegram/README.md`): queue jobs with `telegram/tg.py`, commit + push once, `tg.py wait`. Before reading replies, refresh: queue `getMe` (`--ref inbox-refresh`), push, wait, then `tg.py inbox`. Never AnythingMCP, never getUpdates. Owner chat: `state.json → telegram_chat_id`.

## Story queue (in this order; take `stories.next_story`)

**Patience first (owner, 2026-11-15):** take the next story in the queue that is about patience, affliction or relief after hardship (الصبر / البلاء / الفرج) while one is left; otherwise the next in order. (First applied 2026-11-19: story 2 الأقرع والأبرص والأعمى, sent as two parts `st02` + `st02b`.)

Every number must be **verified** before writing (sunnah.com / dorar.net: the story must really be in Sahih al-Bukhari, with that number or note the correct one). Use the wording of the hadith; never add events, dialogue, names or numbers that are not in the narration.

1. أصحاب الغار الثلاثة والصخرة (البخاري ٢٢٧٢)
2. الأقرع والأبرص والأعمى (البخاري ٣٤٦٤)
3. الرجل الذي سقى كلبًا عطشان فغفر الله له (البخاري ٢٤٦٦)
4. الذي قتل تسعة وتسعين نفسًا ثم تاب (البخاري ٣٤٧٠)
5. جُريج العابد والرضيع الذي تكلّم (البخاري ٣٤٣٦)
6. الرجل الذي أسلف ألف دينار والخشبة في البحر (البخاري ٢٢٩١)
7. حنين الجذع (البخاري ٣٥٨٣–٣٥٨٥)
8. المرأة التي دخلت النار في هرّة (البخاري ٣٤٨٢)
9. الرجل الذي أوصى بنيه أن يحرقوه خوفًا من الله (البخاري ٣٤٨١)
10. الرجل الذي اشترى أرضًا فوجد فيها جرّة ذهب (البخاري ٣٤٧٢)
11. البقرة والذئب اللذان تكلّما (البخاري ٣٤٧١)
12. موسى والخضر عليهما السلام (البخاري ١٢٢ و٣٤٠١)

When the list runs out, propose the next 12 to the owner on Telegram (story hadiths of Sahih al-Bukhari only) and wait for his `ok` before writing.

## T1 — write the next script

1. `git pull`. Read `state.json → stories`. Target date = the next Saturday (if today is Thursday) or Sunday (if today is Friday). If `pending` already exists for that date and is not `skipped`, stop. If `pending` is for an earlier date and was never scheduled, carry its story over (apply any notes).
2. Story N = `stories.next_story` (or the carried-over one). Find the full hadith text in Sahih al-Bukhari and a trusted explanation (فتح الباري لابن حجر first; ابن عثيمين، ابن باز when available). Never invent; leave out anything not in the narration.
3. Write `stories/stNN/script.json` with the schema of `seerah/ep01/script.json`, so `seerah/render_episode.py` renders it:
   - `title` (short Arabic story title), `series_label`: «قصص من صحيح البخاري · القصة N», `tts_model` = `eleven_v4`, `voices`: `{"father": {"voice_id": "YKGG8oefXIWbncG7wgoX", "name": "الراوي"}}` — one narrator (the seerah father's deep warm Fusha voice); every line has `"who": "father"`.
   - **Hook first (owner's rule):** scene 1 opens on the most gripping moment or question of the story («ثلاثة رجال… وصخرة سدّت عليهم باب الغار. كيف نجوا؟»), with `title_card: true`; then the story in order, with tension, then the ending, then one short line with the lesson, then the engagement question. The last scene has `end_card`: «تابعنا لقصة جديدة كل سبت».
   - Say clearly that the Prophet ﷺ told the story («قال رسولُ الله صلّى اللهُ عليهِ وسلّم: …») and keep his key words verbatim where possible.
   - `caption` on each story scene (≤ ~40 chars), `tts` with tashkeel on names and key words, «صلّى الله عليه وسلّم» in full. No `bubble`s (no majlis scene in this series).
   - Images: `prompt`s with ep01's style text (vertical 9:16, warm soft flat storybook, faceless distant figures, no text). **Never depict the Prophet ﷺ, any prophet, the Companions' faces or angels**; for stories about prophets (e.g. موسى والخضر) show places, objects, light, landscapes, distant faceless figures from behind.
   - `sources`: «صحيح البخاري، كتاب …، باب …، ح (رقم)» + the explanation used.
   - **Length:** spoken text for a finished video of **1:30–2:30** (YouTube Shorts allow 3:00).
   - **Always two parts (owner, 2026-11-19), both on Saturday:** Part 1 (11:00) stops at the moment of highest tension and ends «وماذا حدثَ بعدَ ذلك؟ تابِعنا حتى لا يفوتَك الجزءُ الثاني الساعةَ السادسةَ مساءً»; Part 2 (18:00) opens with a one-sentence recap («في الجزء الأول: …», never «بالأمس») and its `end_card` is «قصة جديدة كل سبت». Folders `stNN` + `stNNb`, both in `stories.pending` / `stories.pending_part2` with the same Saturday `publish_date`; `next_story` = N+1 once everything is scheduled.
   - **«فوائد القصة» for the long YouTube video:** write `stories/stNN/benefits.json` = `{"title": "فوائد القصة", "sources": [...], "scenes": [...]}` with the same scene schema (narrator only, captions, images may reuse the story's pictures or 2–3 new calm ones): 5–7 lessons, each from فتح الباري (or ابن عثيمين / ابن باز / other trusted Saudi scholars of Ahl al-Sunnah), faithfully paraphrased with the scholar named, never invented; ~550–750 spoken words so the long video lands at **8–10 min**; last scene = the engagement question + «تابِعنا لتصلَك قصةٌ جديدة كلَّ سبت». Send it with the script (section «📖 فوائد القصة (للفيديو الطويل على يوتيوب)»).
   - *(old rule, kept for reference)* **Two-part stories (TikTok plan, 2026-11-13):** if a story cannot be told well in 2:30 (e.g. موسى والخضر, أصحاب الغار with all three prayers in full), split it into «الجزء الأول» (Saturday) and «الجزء الثاني» (Sunday): Part 1 stops at the moment of highest tension and its last line is «وماذا حدث بعد ذلك؟ نكملها غدًا إن شاء الله»; Part 2 opens with a one-sentence recap. Each part is a full episode in this pipeline (its own script, approval and video); both scripts may be sent in Thursday's T1 run. Titles say «(الجزء 1)» / «(الجزء 2)». **Bookkeeping (first used 2026-11-19):** Thursday's T1 sets `stories.pending` = Part 1 (Saturday, folder `stNN`) and `stories.pending_part2` = Part 2 (Sunday, folder `stNNb`, same shape, status `script_sent`). Friday's T1 sees `pending_part2` for Sunday and stops. Friday's T3, after scheduling Part 1, records it in `published`, then moves `pending_part2` into `pending` (delete `pending_part2`) and does NOT advance `next_story`; Saturday's T2/T3 then handle Part 2 as usual, and `next_story` = N+1 only after Part 2 is scheduled. One owner `ok` to the script message approves both parts.
4. Commit + push. Send the script for review: one `sendMessage` (split if over 3,500 characters) with the title, each scene as «🖼 <المشهد>» + «🎙 الراوي: <النص>», «📚 المصادر», then:
   «📝 سكربت القصة N (<العنوان>) — السبت <التاريخ>: الجزء الأول ١١:٠٠، الجزء الثاني ٦:٠٠ مساءً، والقصة كاملة مع الفوائد على يوتيوب ٨:٠٠ مساءً.
   ✅ للموافقة أرسل: ok
   ✏️ للتعديل: no <ملاحظتك>
   سيُصنع الفيديو بعد موافقتك فقط.»
   Push, `tg.py wait`, store message_ids.
5. Set `stories.pending` = `{"story": N, "publish_date": "<target>", "status": "script_sent", "script_message_ids": [...], "preview_message_ids": [], "notes": [], "messages": []}`. Commit + push.

## T2 — produce the video (only if the script is approved)

1. `git pull`. If `stories.pending` is missing, its `publish_date` is not tomorrow, or its status is not `script_sent`, stop quietly. **Weekly format (2026-11-19):** this run produces FOUR videos for Saturday — steps 3–7 for Part 1 (`stNN`) and Part 2 (`stNNb`), then:
   - **full.mp4 (Facebook):** copy both folders to `stories/_full_NN/` and `_full_NNb/`, drop Part 1's last scene line «وماذا حدث بعد ذلك؟ …» (and its audio), Part 2's recap scene and title card, set `"follow_card": false` on the Part 1 copy, render both and join them (ffmpeg concat filter, re-encode `-preset veryfast -crf 23`, ≤ 0.3 s crossfade) into `stories/stNN/full.mp4`. Delete the `_full_` folders.
   - **long.mp4 (YouTube):** if `benefits.json` is missing (e.g. the first week), write it now (rules in T1) and mention it in the preview message. Generate its voice + images like the story, render it as its own episode folder `stories/stNN_benefits/`, then join full.mp4 (re-rendered without its follow card) + a 2 s title card «فوائد القصة» + the benefits video into `stories/stNN/long.mp4`. Check the length is 8–10 min (if under 8, do not pad: report the length to the owner). Write `stories/stNN/long.txt` (YouTube description: summary, the lessons as a list, sources, links block, 3–5 hashtags) and a 16:9-friendly hook title.
   - **Single-part story (owner, msg 590 on 2026-11-26, first for story 3):** if `stories.pending.format` = `"single"` there is no Part 2 and no `full.mp4`: make `stNN/episode.mp4` (the whole story, may exceed 3:00; Saturday 11:00 on Instagram, TikTok, Threads, Telegram, and Facebook as a video POST if > 90 s — not a YouTube Short) and `long.mp4` (= the episode re-rendered without its follow card + «فوائد القصة», YouTube 20:00 as a normal video). Send both previews with one approval message.
   - Preview: send all four (sendVideo for each ≤ 20 MB, else the commit-pinned raw URL as a link) with one approval message: «✅ ok = الموافقة على الأربعة / ✏️ no <ملاحظتك>».
2. Refresh the inbox; read the owner's replies after `script_message_ids[0]` (careful: the seerah and hadith series use the same chat — only count a reply sent after this script and before any newer script/preview of another series, or one that names the story). `ok` → approved. `no <note>` → apply the note, re-send the script, stop. No reply → send «⏰ تذكير: سكربت القصة N ينتظر موافقتك؛ لن تُنشر غدًا ما لم توافق.» and stop.
3. Images: exactly as seerah S2 step 3 (ElevenLabs `creative_generate_image`, one flow «story-stNN», 9:16, one variation, check every picture: no faces, no prophet/angel, no text; regenerate a bad one once). Save to `stories/stNN/img/<name>.png`.
4. Voice: ElevenLabs `creative_generate_speech`, `model_id` `eleven_v4`, voice `YKGG8oefXIWbncG7wgoX`, **`generations_count: 1`**, never retry by calling twice. Save as `stories/stNN/audio/sNN[a-d].mp3` in script order (as in seerah). If ElevenLabs refuses or the download is blocked, tell the owner on Telegram and stop.
5. Render: copy the series assets the renderer expects if needed (it resolves images relative to the episode folder), run `python3 seerah/render_episode.py stories/stNN --check`, look at every still (captions inside the frame, Arabic shaped, nothing cut), fix, then render `python3 seerah/render_episode.py stories/stNN`. Must be ≤ 2:58 and < 19 MB. Also save the first-scene still with the title card as `stories/stNN/cover.jpg` (from `--check`) — it is the thumbnail.
6. Write `stories/stNN/caption.txt`: line 1 = the hook + « 😳» or « 🤔», line 2 = «💬 » + engagement question, blank, «قصص من صحيح البخاري · القصة N: <العنوان>», a 2–3 sentence summary in own words, «📅 قصة جديدة كل سبت إن شاء الله», «📚 المصادر:», a short call to action (e.g. «اكتب في التعليقات: سبحان الله 🤍، وشارك القصة ليصلك أجرها»), then the links block (root `README.md` → «Links block»), then 3–5 hashtags (e.g. #قصص_إسلامية #قصص_من_صحيح_البخاري #صحيح_البخاري #قصص_للأطفال). **Instagram allows at most 5 hashtags per post (enforced since Dec 2025; more = reduced reach), so use 3–5 relevant hashtags, never more.** Add the line «👨‍👩‍👧 شاهدها مع أطفالك وشاركها مع كل أب وأم» before the call to action (parents share kids' Islamic stories the most). Max 2,000 characters.
7. Commit + push. Preview: `sendVideo` with the commit-pinned raw URL `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/<sha>/stories/stNN/episode.mp4` and caption «🎬 القصة N — <العنوان> — الجزء N يُنشر السبت ١١:٠٠ / ٦:٠٠ مساءً», then a `sendMessage`:
   «✅ للموافقة على النشر أرسل: ok
   ❌ للرفض مع ملاحظة: no <ملاحظتك>
   ⏰ تُفحص موافقتك مرة واحدة الساعة ١:٢٥ ظهر يوم النشر، فأرسل ردّك قبلها.
   لن يُنشر شيء قبل موافقتك.»
   Push, wait, store `preview_message_ids`, status `video_sent`. Commit + push.

## T3 — check approval and schedule

Runs **the evening before** the publishing day (Friday ~23:23 Istanbul). **Weekly format (2026-11-19):** on `ok`, schedule Part 1 as below for **11:00**, Part 2 the same way for **18:00** (its own caption/TikTok/Threads/Telegram posts, Telegram `--not-before <day>T14:55:00Z`), the Facebook full story as ONE separate post at **11:00** (providers facebook only, `facebookData {"type":"POST"}`, media `full.mp4`, text = Part 1 caption with the hook adapted to the whole story; Part 1 and Part 2 posts then do NOT include facebook as a Reel, only the Facebook Story), and the long video at **20:00** (providers youtube only, `youtubeData` type `"video"`, title ≤ 100 chars, description `long.txt`, `madeForKids false`, category EDUCATION). Record all four in `stories.published`. "The publishing day" = the next calendar day in Istanbul (if the run starts after midnight but before 11:00, it is today). Publish time is **11:00 Europe/Istanbul**.

1. `git pull`. If `stories.pending` is missing, its `publish_date` is not the publishing day, or status is not `video_sent`, stop quietly.
2. Refresh the inbox; read replies after `preview_message_ids[0]`; save them.
3. `ok` → Metricool `createScheduledPost` (blogId `state.json → metricool_blog_id`), ONE post, providers instagram + youtube (TikTok gets its own post, see below), **the publishing day 11:00 Europe/Istanbul**:
   - media: commit-pinned raw URL of `episode.mp4`; text: `caption.txt` as-is; `videoThumbnailUrl`: commit-pinned raw URL of `cover.jpg` (only if the file exists)
   - instagramData `{"type":"REEL","showReelOnFeed":true}`
   - youtubeData `{"title":"<curiosity hook> | قصة من صحيح البخاري" (≤100 chars; a striking moment then a question or a surprise, like «ثلاثة رجال سدّت عليهم صخرةٌ باب الغار… فكيف نجوا؟ 😳 | قصة من صحيح البخاري»; only what the hadith says),"type":"short","privacy":"public","category":"EDUCATION","madeForKids":false,"tags":[...]}`
   - tiktokData `{"title":"<same hook, shorter>","privacyOption":"PUBLIC_TO_EVERYONE","autoAddMusic":false}`
   **TikTok gets its own post and its own caption (owner's request 2026-11-13, TikTok plan):** do NOT put tiktok in the same Metricool post. Schedule a SECOND `createScheduledPost` at the same time with providers **tiktok only**, the same media (and `videoThumbnailUrl` if used above), and as `text` the TikTok caption below; the first post keeps the other providers. TikTok caption (≤ 600 characters — TikTok search reads the first line and the hashtags, people do not read long text):
   - line 1: the hook question or striking moment + one emoji, with the words people search for (e.g. «حديث نبوي», «قصة من صحيح البخاري», «السيرة النبوية», the topic word);
   - line 2: «💬 » + the engagement question;
   - line 3: the series line («📖 الحديث N من صحيح البخاري بالترتيب» / «🎬 السيرة النبوية للأطفال · الحلقة N» / «🕌 قصص من صحيح البخاري · القصة N») + «تابعنا للحلقة القادمة 🤍»;
   - line 4: «📚 » + the short source (book + number), no long text;
   - line 5: 4–5 hashtags only, relevant ones (e.g. #حديث_نبوي #صحيح_البخاري #قصص_اسلامية #السيرة_النبوية #اسلام), never a long tag list.
   Save it next to the main caption as `<name>.tiktok.txt` and commit it. tiktokData stays as below (no added music).
   Then queue the same video + caption for @HadithDailyAr: `tg.py queue sendVideo '{"chat_id":"@HadithDailyAr","video":"<url>","caption":"<caption>","supports_streaming":true}' --ref story-stNN --not-before <publishing day>T07:55:00Z` (split as in seerah if the caption is over 1024 characters). The bridge sends due jobs on its own 15-minute schedule and on the hourly tick pushed by the Level Up task (:25), so the channel post goes out between 11:00 and ~11:25; that is fine. **Telegram channel version (owner's Telegram plan 2026-11-13):** remove the hashtag line(s) from the caption and end it with «📢 شارك القناة: t.me/HadithDailyAr» + newline + «فالدال على الخير كفاعله 🤍».
   Record `stories.published.stNN` (`publish_at`, `metricool_post_id`, `telegram_job`, `approved`), status `scheduled`, `next_story` = N+1, and tell the owner «✅ جُدولت القصة N ليوم السبت: الجزء الأول ١١:٠٠ والجزء الثاني ٦:٠٠ مساءً (إنستغرام، تيك توك، شورتس، ثريدز، تيليغرام)، القصة كاملة على فيسبوك ١١:٠٠، والفيديو الطويل مع الفوائد على يوتيوب ٨:٠٠ مساءً.» + «📂 أضف القصة إلى قائمة التشغيل "قصص من صحيح البخاري" في يوتيوب (أنشئها عند أول قصة إن لم تكن موجودة).»
4. `no <note>` → status `skipped`, keep the note; the next T1 redoes the story with it; tell the owner.
5. No reply → nothing is published; do not mark it skipped; send the owner one short reminder that the story will not be published at 11:00 unless he replies ok, and stop.
6. Never publish a story the owner did not approve.

**Names (owner, 2026-11-23):** every narrated line follows root `README.md` → «Pronunciation of names» (bracket direction, trim the spoken tail, check the first vowel with `tool/check_vowel.py`).
