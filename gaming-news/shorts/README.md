# Level Up — daily gaming-news Short

One vertical Short per day (English, ~25–40 s) for **Level Up**: Telegram channel `@LevelUpGames0` (posted automatically) and YouTube **Level Up | Gaming News** `@LevelUpGamesNews` (see "YouTube" below). Built from the stories the hourly news run already posted to the channel, so every fact has a source.
Separate from the hadith project — never touch hadith/seerah/stories files or `state.json` except `state.json → telegram_chat_id` (read only).

Files: `make_short.py` (renderer) · `epYYYY-MM-DD/` (one folder per day: `short.json`, `audio/`, `img/`, `short.mp4`, `youtube.txt`) · `done.txt` (one line per day: date, YouTube title, stories).

## Format (owner-approved 2026-11-14, based on the niche research)
- **Hook in the first second:** the video opens directly on story #1 with the banner "N GAMING STORIES · NN SEC" — no logo intro.
- **3 stories** (2 on a slow day, 4 max), biggest first. One chip per story on the configurator bar; the right arrow "clicks" and the panel slides to the next story (style of @dmytro.edits' car-configurator reel).
- **AI voiceover** (ElevenLabs, voice **Alex** `6sWNMlBf4TdebygSxQGj`, model `eleven_v4`, `generations_count: 1`, never retry a generation): one clip per story + one outro clip. Story #1's clip starts with the hook line.
- Headline on screen = the same fact the voice says, in my own words, ≤ 90 characters. Source line under it.
- Outro (~4 s): "Which one surprised you most? Comment below" + follow @LevelUpGamesNews. The CTA changes a little every day.
- Length 25–40 s. Text stays in the safe zone (the renderer handles it).

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
