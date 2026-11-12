# «قصص من صحيح البخاري» — runbooks for the scheduled runs

Owner's new series (decided 2026-11-13, after comparing the channel with the top Arabic Islamic channels: the narrated *story* hadiths of Sahih al-Bukhari reach millions of views, while plain hadith + explanation videos stay in the hundreds; the seerah episode in this style was the channel's best video). It runs **next to** the hadith series (Mon/Wed/Fri) and the seerah series (Tue/Thu); it replaces neither.

Each episode tells ONE story that the Prophet ﷺ told or that is narrated in **Sahih al-Bukhari**, as a narrated short film: still illustrations in the seerah style (warm soft flat storybook, faceless figures), slow camera moves, one narrator voice, short on-screen captions. No music, ever. Everything the owner sees is in Arabic; his reply words are English (`ok` / `no <note>`).

**Schedule:** one story on **Saturday and Sunday at 14:00 Europe/Istanbul** (`state.json → stories.days`, `stories.slot`) on Instagram (Reel) + YouTube (Short) + TikTok + the Telegram channel @HadithDailyAr.

**Pipeline — 3 scheduled runs, every step needs the owner's approval** (same rules as the seerah series):

| Run | When (Istanbul) | Does |
|---|---|---|
| T1 script | Thu + Fri ~20:17 | writes the script of the next story and sends it for review (Thu → Saturday's story, Fri → Sunday's) |
| T2 production | Fri + Sat ~19:53 | if the script is approved: images, voice, render, caption, sends the preview video |
| T3 approval | Sat + Sun ~13:23 | if the video is approved: schedules it for 14:00 the same day |

`state.json → stories` = `{"days": ["Sat","Sun"], "slot": "14:00", "next_story": 1, "pending": {...} | null, "published": {}}`; `pending` = `{"story": N, "publish_date": "YYYY-MM-DD", "status": "script_sent" | "video_sent" | "scheduled" | "skipped", "script_message_ids": [], "preview_message_ids": [], "notes": [], "messages": []}`.

Telegram goes ONLY through the GitHub bridge (`telegram/README.md`): queue jobs with `telegram/tg.py`, commit + push once, `tg.py wait`. Before reading replies, refresh: queue `getMe` (`--ref inbox-refresh`), push, wait, then `tg.py inbox`. Never AnythingMCP, never getUpdates. Owner chat: `state.json → telegram_chat_id`.

## Story queue (in this order; take `stories.next_story`)

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
   - **Hook first (owner's rule):** scene 1 opens on the most gripping moment or question of the story («ثلاثة رجال… وصخرة سدّت عليهم باب الغار. كيف نجوا؟»), with `title_card: true`; then the story in order, with tension, then the ending, then one short line with the lesson, then the engagement question. The last scene has `end_card`: «تابعنا لقصة جديدة كل سبت وأحد».
   - Say clearly that the Prophet ﷺ told the story («قال رسولُ الله صلّى اللهُ عليهِ وسلّم: …») and keep his key words verbatim where possible.
   - `caption` on each story scene (≤ ~40 chars), `tts` with tashkeel on names and key words, «صلّى الله عليه وسلّم» in full. No `bubble`s (no majlis scene in this series).
   - Images: `prompt`s with ep01's style text (vertical 9:16, warm soft flat storybook, faceless distant figures, no text). **Never depict the Prophet ﷺ, any prophet, the Companions' faces or angels**; for stories about prophets (e.g. موسى والخضر) show places, objects, light, landscapes, distant faceless figures from behind.
   - `sources`: «صحيح البخاري، كتاب …، باب …، ح (رقم)» + the explanation used.
   - **Length:** spoken text for a finished video of **1:30–2:30** (YouTube Shorts allow 3:00).
4. Commit + push. Send the script for review: one `sendMessage` (split if over 3,500 characters) with the title, each scene as «🖼 <المشهد>» + «🎙 الراوي: <النص>», «📚 المصادر», then:
   «📝 سكربت القصة N (<العنوان>) — تُنشر <اليوم والتاريخ> الساعة ١٤:٠٠.
   ✅ للموافقة أرسل: ok
   ✏️ للتعديل: no <ملاحظتك>
   سيُصنع الفيديو بعد موافقتك فقط.»
   Push, `tg.py wait`, store message_ids.
5. Set `stories.pending` = `{"story": N, "publish_date": "<target>", "status": "script_sent", "script_message_ids": [...], "preview_message_ids": [], "notes": [], "messages": []}`. Commit + push.

## T2 — produce the video (only if the script is approved)

1. `git pull`. If `stories.pending` is missing, its `publish_date` is not tomorrow, or its status is not `script_sent`, stop quietly.
2. Refresh the inbox; read the owner's replies after `script_message_ids[0]` (careful: the seerah and hadith series use the same chat — only count a reply sent after this script and before any newer script/preview of another series, or one that names the story). `ok` → approved. `no <note>` → apply the note, re-send the script, stop. No reply → send «⏰ تذكير: سكربت القصة N ينتظر موافقتك؛ لن تُنشر غدًا ما لم توافق.» and stop.
3. Images: exactly as seerah S2 step 3 (ElevenLabs `creative_generate_image`, one flow «story-stNN», 9:16, one variation, check every picture: no faces, no prophet/angel, no text; regenerate a bad one once). Save to `stories/stNN/img/<name>.png`.
4. Voice: ElevenLabs `creative_generate_speech`, `model_id` `eleven_v4`, voice `YKGG8oefXIWbncG7wgoX`, **`generations_count: 1`**, never retry by calling twice. Save as `stories/stNN/audio/sNN[a-d].mp3` in script order (as in seerah). If ElevenLabs refuses or the download is blocked, tell the owner on Telegram and stop.
5. Render: copy the series assets the renderer expects if needed (it resolves images relative to the episode folder), run `python3 seerah/render_episode.py stories/stNN --check`, look at every still (captions inside the frame, Arabic shaped, nothing cut), fix, then render `python3 seerah/render_episode.py stories/stNN`. Must be ≤ 2:58 and < 19 MB. Also save the first-scene still with the title card as `stories/stNN/cover.jpg` (from `--check`) — it is the thumbnail.
6. Write `stories/stNN/caption.txt`: line 1 = the hook + « 😳» or « 🤔», line 2 = «💬 » + engagement question, blank, «قصص من صحيح البخاري · القصة N: <العنوان>», a 2–3 sentence summary in own words, «📅 قصة جديدة كل سبت وأحد إن شاء الله», «📚 المصادر:», a short call to action (e.g. «اكتب في التعليقات: سبحان الله 🤍، وشارك القصة ليصلك أجرها»), then 8–12 hashtags (#قصص_إسلامية #قصص_من_صحيح_البخاري #صحيح_البخاري #قصص_الأنبياء when it fits #حديث_نبوي #قصص_مؤثرة …). Max 2,000 characters.
7. Commit + push. Preview: `sendVideo` with the commit-pinned raw URL `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/<sha>/stories/stNN/episode.mp4` and caption «🎬 القصة N — <العنوان> — تُنشر <اليوم> ١٤:٠٠», then a `sendMessage`:
   «✅ للموافقة على النشر أرسل: ok
   ❌ للرفض مع ملاحظة: no <ملاحظتك>
   ⏰ تُفحص موافقتك مرة واحدة الساعة ١:٢٥ ظهر يوم النشر، فأرسل ردّك قبلها.
   لن يُنشر شيء قبل موافقتك.»
   Push, wait, store `preview_message_ids`, status `video_sent`. Commit + push.

## T3 — check approval and schedule

1. `git pull`. If `stories.pending` is missing, its `publish_date` is not today, or status is not `video_sent`, stop quietly.
2. Refresh the inbox; read replies after `preview_message_ids[0]`; save them.
3. `ok` → Metricool `createScheduledPost` (blogId `state.json → metricool_blog_id`), ONE post, providers instagram + youtube + tiktok, **today 14:00 Europe/Istanbul**:
   - media: commit-pinned raw URL of `episode.mp4`; text: `caption.txt` as-is; `videoThumbnailUrl`: commit-pinned raw URL of `cover.jpg` (only if the file exists)
   - instagramData `{"type":"REEL","showReelOnFeed":true}`
   - youtubeData `{"title":"<curiosity hook> | قصة من صحيح البخاري" (≤100 chars; a striking moment then a question or a surprise, like «ثلاثة رجال سدّت عليهم صخرةٌ باب الغار… فكيف نجوا؟ 😳 | قصة من صحيح البخاري»; only what the hadith says),"type":"short","privacy":"public","category":"EDUCATION","madeForKids":false,"tags":[...]}`
   - tiktokData `{"title":"<same hook, shorter>","privacyOption":"PUBLIC_TO_EVERYONE","autoAddMusic":false}`
   Then queue the same video + caption for @HadithDailyAr: `tg.py queue sendVideo '{"chat_id":"@HadithDailyAr","video":"<url>","caption":"<caption>","supports_streaming":true}' --ref story-stNN --not-before <today>T10:55:00Z` (split as in seerah if the caption is over 1024 characters). The bridge sends due jobs on its own 15-minute schedule and on the hourly tick pushed by the Level Up task (:25), so the channel post goes out between 14:00 and ~14:25; that is fine.
   Record `stories.published.stNN` (`publish_at`, `metricool_post_id`, `telegram_job`, `approved`), status `scheduled`, `next_story` = N+1, and tell the owner «✅ جُدولت القصة N لليوم الساعة ١٤:٠٠ على إنستغرام ويوتيوب وتيك توك وقناة تيليغرام.» + «📂 أضف القصة إلى قائمة التشغيل "قصص من صحيح البخاري" في يوتيوب (أنشئها عند أول قصة إن لم تكن موجودة).»
4. `no <note>` → status `skipped`, keep the note; the next T1 redoes the story with it; tell the owner.
5. No reply → nothing is published; status `skipped`; tell the owner the story moves to the next Saturday/Sunday.
6. Never publish a story the owner did not approve.
