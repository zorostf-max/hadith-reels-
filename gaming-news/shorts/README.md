# Level Up — daily gaming-news Short

One vertical Short per day (English, ~25–40 s) for **Level Up**: Telegram channel `@LevelUpGames0` (posted automatically) and YouTube **Level Up | Gaming News** `@LevelUpGamesNews` (see "YouTube" below). Built from the stories the hourly news run already posted to the channel, so every fact has a source.
Separate from the hadith project — never touch hadith/seerah/stories files or `state.json` except `state.json → telegram_chat_id` (read only).

Files: `make_short.py` (renderer) · `epYYYY-MM-DD/` (one folder per day: `short.json`, `audio/`, `img/`, `short.mp4`, `youtube.txt`) · `done.txt` (one line per day: date, YouTube title, stories).

## Follow plan (owner's decision 2026-11-19: viewers watch but don't follow) — every Level Up reel (regular and breaking)

1. **Spoken follow line at the end:** the outro voice clip = the comment question + «Follow Level Up so you never miss gaming news, four times a day.» (breaking reels: «Follow Level Up for breaking gaming news.»). One generation for the whole outro clip (generations_count 1).
2. **FOLLOW button:** built into `make_short.py`'s outro card (pulsing «+ FOLLOW» under @LevelUpGamesNews). Check it on the `--check` sheet.
3. **Caption line 2** (right after the hook line, on YouTube/Instagram/Facebook and in the TikTok text): «📌 Follow for gaming news 4× a day 🎮». Threads/Bluesky: add «Follow for daily gaming news» only if it fits the 300-character limit.


## Format (owner-approved 2026-11-14, based on the niche research)
- **Hook in the first second:** the video opens directly on story #1 with the banner "N GAMING STORIES · NN SEC" — no logo intro.
- **3 stories** (2 on a slow day, 4 max), biggest first.
- **Look = TECH style v2 (owner's request 2026-11-15, replaces the orange car-configurator look):** full-screen HUD over an animated **solar-panel grid** background. Every story is its own page with its own colour from `cat` (Nintendo red, PlayStation blue, Xbox green, hardware/PC lime, esports purple, deals yellow, games orange, tech cyan) — so always set `cat` correctly. Page header `01/03 NINTENDO` + tag, a "monitor" card with corner brackets for the art, typewriter headline, `> SOURCE:` line, glitch-scan transition between pages. Fonts are in `shorts/fonts/` (Orbitron, JetBrains Mono, Rajdhani).
- **AI voiceover** (ElevenLabs, voice **Alex** `6sWNMlBf4TdebygSxQGj`, model `eleven_v4`, `generations_count: 1`, never retry a generation): one clip per story + one outro clip. Story #1's clip starts with the hook line.
- Headline on screen = the same fact the voice says, in my own words, ≤ 90 characters. Source line under it.
- Outro (~4 s): "Which one surprised you most? Comment below" + follow @LevelUpGamesNews. The CTA changes a little every day.
- Length 25–40 s. Text stays in the safe zone (the renderer handles it). If the clips run long, speed the story clips up with `ffmpeg -filter:a atempo=1.15` (pitch kept) instead of regenerating (used 2026-11-21 18:00).

## FOUR REELS A DAY (owner's request 2026-11-18) — supersedes "one per day" above
- Slots **10:00, 14:00, 18:00, 22:00 Europe/Istanbul**; each run fires ~47 min before its slot. Each reel = the 2–3 biggest stories since the previous reel (never a story already used in an earlier reel, in a breaking reel, or in this brand's Metricool posts of the last 36 h, unless there is a genuinely new development).
- **Per-slot folder:** `epYYYY-MM-DD-HHMM/` (e.g. `ep2026-11-18-1000/`), so the four reels never overwrite each other; `done.txt` line starts with `YYYY-MM-DD HH:MM`.
- **Hook card (owner's request 2026-11-18):** every reel opens with a full-screen hook card — add to `short.json`:
  `"hook": {"text": "<= 6 words, the most striking fact/number/name>", "kicker": "BREAKING|TGA 2026|…", "cat": "<cat>", "audio": "audio/hook.mp3"}`.
  `make_short.py` renders it as its own ~2–3.2 s page (very large Orbitron 900, black stroke, accent glow, slam-in) before story 1. Its voice clip `audio/hook.mp3` is a separate ElevenLabs generation of ≤ 8 words (e.g. "[energetic] GTA 6 just broke a record."); story 1's clip then starts "Three gaming stories you missed. Number one: …".
- Publishing is through **Metricool** (blogId 8168112): one post YouTube Short + Instagram Reel + Facebook Reel; a separate Threads + Bluesky post (text ≤ 300 chars). No Metricool TikTok post (the owner posts TikTok by hand, see below). **X too (owner's request 2026-11-19, test video post published OK):** a SEPARATE Metricool post at the same time, providers `[{"network":"twitter"}]` (account @AbdulbariH2771), the same video in media, `twitterData {"tags":[]}`, English text ≤ 270 chars (hook fact + one line on the other stories + a short question + 2 hashtags, no link; "reportedly" for unconfirmed facts). If X fails, skip it and mention it in the owner message. The "YouTube — published through Claude in Chrome" section below is no longer used by the slot runs.
- If WebFetch is unavailable in an unattended run, the facts can come from the hourly run's own channel captions (recover them with `git log` / `git show` of the committed `telegram/outbox/*.json` jobs), cross-checked with WebSearch result titles; anything that is not clearly confirmed is worded "reportedly".

## TikTok — sent to the owner on Telegram, he publishes it by hand (owner's decision 2026-11-19, replaces the 2026-11-18 version and automatic TikTok publishing)
- **No Metricool TikTok post.** At the end of each slot run, send the owner in his PRIVATE chat (`state.json → telegram_chat_id`), through the bridge (same push as the channel post or a following one; the owner wants every TikTok reel, so it is sent even for a night slot):
  1. `sendVideo` with the reel's public raw URL (≤ 20 MB, else the URL as text via `--fallback-text`), caption «🎵 ريل تيك توك لـ Level Up — الساعة HH:MM» + newline + «انشره بنفسك 👇».
  2. `sendMessage` with the ready-to-copy text, exactly in this shape (English text, Arabic labels):
     `العنوان:` / <English hook title ≤ 90 chars> / `الوصف:` / <hook line + 1 line of facts (no unverified figures as fact) + a question> / <1–2 @mentions of official TikTok accounts, only if sure> / <6–8 hashtags incl. #gamingnews #gaming #fyp> / `✅ فعّل «AI-generated content»` — plus `🔞 فعّل Audience controls 18+` ONLY for a mature-rated game, horror, violence-related news or gambling.
- Content rules still apply: mature-rated games (GTA, Call of Duty, Mortal Kombat, horror…): no violence, weapons, blood, gore, drugs or crime scenes in the visuals or thumbnail — logo/key art without violence, text cards and numbers only. Prefer a non-mature lead story when one is equally big.
- Never present estimates, analyst figures, leaks or rumours as official numbers — write "reportedly", "estimated", "rumored" or name the estimator, in voice, on-screen text, title and captions.

## YouTube title length (owner's request 2026-11-18)
- After YouTube rejected a 101-character title ("invalid or empty video title"): the YouTube title INCLUDING " #shorts" and every emoji/symbol must be **≤ 90 characters**. Count it with code before scheduling (`python3 -c "print(len('''<title>'''))"`); if over 90, shorten it (keep the lead story only) and count again. Never use `<` or `>` in the title. Write the same checked title in `youtube.txt`.

## RUNBOOK — daily run (21:24 Istanbul, published at about 21:45)
1. `cd` into the repo, `git pull`. If `gaming-news/shorts/done.txt` already has today's date, stop.
2. **Pick the stories:** read `gaming-news/posted.txt`, take the links posted in the last 24 h (skip `(same story)` lines). Choose the 3 **biggest** (same "big story" test as the X tweets in `gaming-news/README.md`: GTA 6/Rockstar, platform news, major release/reveal/delay, big industry move, striking number, big GPU/console price change, major esports result). Prefer stories with a striking number or a clear image. Never a story already used in an earlier Short (check `done.txt`).
3. Re-read each chosen article with WebFetch and write only facts the source states. Never invent numbers, dates or quotes.
4. Make `gaming-news/shorts/epYYYY-MM-DD/short.json` (schema at the top of `make_short.py`):
   - `tag` ≤ 9 chars, `cat` from the list, `head` ≤ 90 chars, `src` = "source: <Site>" (two sites max).
   - `art`: use a data type when the story has a number (`counter`, `bars`, `stat`), `progress` for downloads/pre-loads/launches, `pills` for showcases/Directs with several reveals, `split` for graphics tech. Otherwise `image` with the article's image downloaded to `img/sN.jpg` (`curl -sSfL`); check the picture is not a logo, a tiny thumbnail or contains a person's face in close-up; if it fails, use `stat` with the key fact instead.
5. **Voice:** `creative_create_flow` named `levelup-short-YYYY-MM-DD`, then one `creative_generate_speech` per story and one for the outro on that flow (voice/model above, `generations_count: 1`, start the prompt with `[energetic]`, outro with `[upbeat]`). Script, short and spoken (numbers written out the way they are said):
   - story 1: "N gaming stories you missed today. Number one: <fact in ≤ 25 words>."
   - story 2: "Number two: <fact>."  · last story: "And number three: <fact>."
   - outro: one question + "follow Level Up for gaming news every day."
   Poll `creative_get_flow_run_status` once all are started, download every `content_url` with `curl -sSfL -o audio/sN.mp3` (`audio/outro.mp3`). If ElevenLabs refuses (credits) or a download is blocked, send the owner a short Arabic Telegram message through the bridge and stop — never publish a silent Short.
6. `python3 gaming-news/shorts/make_short.py gaming-news/shorts/epYYYY-MM-DD --check` and look at `check_sheet.png`: nothing overlapping, numbers right, text inside the frame. Fix `short.json`, check again, then render without `--check`. Must be < 19 MB (Telegram URL limit 20 MB). Delete the `check_*.png` files before committing.
7. Write `youtube.txt`:
   ```
   TITLE: <≤ 70 chars, curiosity-first, the biggest fact first, no clickbait lies> #shorts
   ---
   <2–3 lines: the stories in one line each>
   📰 Sources: <Site> <link> · <Site> <link> · …
   🔔 Daily gaming news: subscribe @LevelUpGamesNews · Telegram t.me/LevelUpGames0
   #GamingNews #<Game> #<Company> #shorts
   ---
   TAGS: gaming news, <game>, <company>, … (8–12)
   ```
8. Commit + push (`git add gaming-news/shorts && git commit -m "short: YYYY-MM-DD" && git push`, pull --rebase and retry once if rejected). Use the commit-pinned raw URL `https://raw.githubusercontent.com/zorostf-max/hadith-reels-/<sha>/gaming-news/shorts/epYYYY-MM-DD/short.mp4`.
9. Telegram (bridge, `telegram/README.md`):
   - Channel: `sendVideo` to `@LevelUpGames0` with caption (HTML): `🎬 <b>Today in gaming: N stories in NN seconds</b>` + one line per story + `🔔 <a href="https://t.me/LevelUpGames0">@LevelUpGames0</a>` + `#GamingNews`; no `--not-before` (posted as soon as the Short is ready).
   - Owner: only the YouTube result line (section YouTube) — or the fallback message with the video + `youtube.txt`.
   - Push, then `tg.py wait` the jobs.
10. Append `YYYY-MM-DD<TAB>title<TAB>tags of the stories` to `done.txt`, commit + push.

## YouTube — published through Claude in Chrome (tested 2026-11-14)
The owner chose (2026-11-14) to publish the Short on **Level Up | Gaming News** (channel id `UCwRDrrCzN-3L2WWp23F163Q`) through his own Chrome with the Claude in Chrome extension (a test upload worked). vidIQ/Metricool are not connected for this channel.

In step 9, after the Telegram jobs are queued:
1. Make the upload copy (Claude in Chrome's file upload takes at most 3.8 MB): `ffmpeg -y -i short.mp4 -vf scale=720:1280 -c:v libx264 -preset veryfast -b:v 650k -maxrate 750k -bufsize 1500k -c:a aac -b:a 96k -movflags +faststart short_720.mp4` → must be < 3.6 MB (lower `-b:v` if not). Do not commit it.
2. Load the chrome-browser skill, then `tabs_context_mcp` (createIfEmpty) → if the extension is not connected or does not answer, skip to the fallback.
3. Navigate a new tab to `https://studio.youtube.com`. Check the top-right account button says **Level Up | Gaming News** (never upload to the hadith channel; if it is another channel, stop and use the fallback).
4. Click the "تحميل فيديوهات" / upload button, `find` the hidden file input and `file_upload` the absolute path of `short_720.mp4` (origin `https://studio.youtube.com`).
5. Set the texts with javascript_tool (typing into these boxes is unreliable):
   ```js
   function setBox(id, text){const b=document.querySelector(`ytcp-uploads-dialog #${id} #textbox[contenteditable]`); b.focus(); document.execCommand('selectAll'); document.execCommand('insertText', false, text); b.blur(); return b.innerText;}
   [setBox('title-textarea', TITLE), setBox('description-textarea', DESCRIPTION)]
   ```
   TITLE/DESCRIPTION from `youtube.txt` (title ≤ 100 chars). Then click `tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]`.
   Playlists (created 2026-11-15): open the upload dialog's Playlists dropdown, tick **Daily Gaming News** always, plus the topic list of story #1 when it fits (**GTA 6 News**, **PC Hardware & GPU News**, **PlayStation, Xbox & Nintendo**, **Esports**), then click the dropdown's done button. If the dropdown does not work, skip it and say so in the owner message. The upload defaults (category Gaming, English, tags, Public) are already set on the channel.
6. Click `#next-button` three times (1.5 s apart), click `tp-yt-paper-radio-button[name="PUBLIC"]`, take a screenshot to check title, preview and "Public", then click `#done-button`. Wait for the confirmation, then read the short link (`https://youtube.com/shorts/<id>`) from the dialog or from Studio → Content.
7. Close the tab. Send the owner one Arabic line through the bridge: «✅ نُشر شورت اليوم على يوتيوب: <link>» + the pinned-comment text from the channel doc to paste (comments cannot be pinned reliably by the run).
- **Fallback** (extension not connected, wrong channel, upload or save fails after 2 tries): send the owner the video + `youtube.txt` in his private chat for a manual upload, and say in one line why the automatic upload did not happen. Never leave a half-finished upload: if the dialog is open, close it (a draft may stay — mention it).
The Telegram channel post happens in every case.
