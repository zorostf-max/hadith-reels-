# Level Up — gaming news for Telegram

Automatic gaming news for the owner's Telegram channel **Level up** (`@LevelUpGames0`, chat id `-1003872817226`), posted by the bot `@my_cs2_monitor_bot` through the **GitHub Actions Telegram bridge** (`telegram/README.md`) — not AnythingMCP.
This folder is separate from the hadith reels project in the rest of the repo — never touch the hadith files, `state.json` or the hadith Telegram approval flow from here.

Owner's rules (2026-11-09):
- Post **each news item on its own, as soon as it comes out**: a run every hour (:25, the shortest interval scheduled tasks allow), posting **every** qualifying new story, not just a few (owner's request 2026-11-12).
- Post **directly** to the channel, no approval step.
- Write in **English**, always with the item's **publish time**, **all the sources** that cover the story, **hashtags** and **mentions** of the official accounts involved (owner's request 2026-11-12).
- Topics: game news and releases · esports and tournaments (CS2, Valorant, LoL…) · PC hardware and graphics cards · platforms and deals (PlayStation, Xbox, Nintendo, Steam, free games, big discounts).

Files: `tweets.txt` (log of links whose tweet was sent to the owner) · `fetch_news.py` (reads the RSS feeds, prints fresh items as JSON with an image URL) · `posted.txt` (log of every link already posted or skipped as a duplicate — one line per link: `time<TAB>source<TAB>url`).

## RUNBOOK — hourly run

1. `cd` into the repo, `git pull`. If `gaming-news/pending.txt` exists, first reconcile it (instructions inside) — never re-queue its stories. `pip install --break-system-packages -q feedparser` if it is missing.
2. `python3 gaming-news/fetch_news.py --hours 2 --limit 30`. It already drops links in `posted.txt`.
3. Choose what to post (**every qualifying new story, up to 6 per run**, oldest first, so nothing waits for a later run):
   - **Keep** real news in the four topics above.
   - **Skip**: walkthroughs/guides ("how to find…", "all locations…"), redeem-code lists, quizzes and NYT puzzle answers, opinion/review pieces with no news, non-gaming stories (food, animals, general politics, film/TV unless it is a game adaptation), small affiliate deals. Do not log skipped items; they age out of the 2-hour window on their own.
   - **One story = one post, built from all its sources.** Group the items in this run's list that cover the same story: write ONE post that combines the facts from all of them (read each with WebFetch if the summaries are thin) and list every one of them under 📰 Sources. Log the first link normally and the others as `(same story)`. If the story was already posted in the last day (check `posted.txt`), do not post again — just log the new links as `(same story)`.
   - If nothing qualifies, post nothing, but still push the tick job of step 6.
4. For each chosen item, if the RSS summary is too thin to write two accurate sentences, read the article with WebFetch. Write only facts the source states; never invent numbers, dates or quotes.
5. For each item queue a `sendPhoto` job (`python3 telegram/tg.py queue sendPhoto '{"chat_id":"@LevelUpGames0","photo":"<image>","parse_mode":"HTML","caption":"…"}' --ref news-<slug> --fallback-text "<same caption>"`), then commit + push once and run `python3 telegram/tg.py wait <all job names>`. Caption (≤ 1024 chars) in this shape — own words, no copied sentences, at most one short quote under 15 words:

   ```
   <emoji> <b>Headline in my own words</b>

   2–4 short sentences combining the facts from all sources: what happened, the key details, why it matters.

   🕒 Nov 12, 2026 · 19:32 (GMT+3)
   📰 Sources: <a href="LINK1">GameSpot</a> · <a href="LINK2">IGN</a> · <a href="LINK3">PC Gamer</a>
   👥 <a href="https://x.com/RockstarGames">@RockstarGames</a> · <a href="https://x.com/PlayStation">@PlayStation</a>

   CALL TO ACTION

   #GTA6 #Rockstar #PS5 #GamingNews
   ```
   - 🕒 = the **earliest** `published_utc` of the story's items, converted to Istanbul time (GMT+3). With a single source write `📰 Source:`.
   - **👥 Mentions** (owner's request 2026-11-12): 1–3 **official X accounts** of the studios, publishers, platforms, teams, tournaments or people the story is about. Take them from `gaming-news/handles.txt` (verified list); for a name not in it, confirm the official handle with one WebSearch and, if confirmed, add it to `handles.txt`; if you cannot confirm it, leave it out — never guess. Always write a mention as a link `<a href="https://x.com/HANDLE">@HANDLE</a>`: a bare `@name` in Telegram points to a Telegram user, who may be someone else. Omit the 👥 line if no official account fits.
   - **Hashtags**: 3–5 — the game or product, the company or team, the platform or event, then always `#GamingNews` last. CamelCase, no spaces or punctuation inside a tag.
   CALL TO ACTION (owner's request 2026-11-11) is one short English line asking for a reaction and a comment, tied to the story and varied every post, e.g. "🔥 React if you're hyped · 💬 Will you play it day one?", "👍 Like if you want this on PC · 💬 Tell us below", "💰 Worth it? React 👍 or 👎 and comment your take".
   The time is the item's `published_utc` converted to Istanbul time (GMT+3). Emoji by topic: 🎮 games · 🏆 esports · 🖥️ PC hardware · 🕹️ platforms · 💸 deals. Escape `&`, `<`, `>` in the text.
   The `--fallback-text` makes the bridge send the caption as a text message if Telegram refuses the photo. Never queue the same item twice.
6. **Always** (even when there is no news) queue one tick job — `python3 telegram/tg.py queue getMe '{}' --ref tick` — in the same push, so the bridge runs every hour and sends any timed jobs that are due (GitHub's own timer is unreliable).
   For each job that `wait` reports as ok, append its line to `posted.txt` (time in GMT+3, source, link). Then `git add gaming-news && git commit -m "news: N posts" && git push` (pull --rebase and retry once if the push is rejected).
7. If a feed in `feed_errors` keeps failing, or the bot cannot post (e.g. it lost admin rights), queue one short `sendMessage` to the owner (`state.json` → `telegram_chat_id`) — at most once a day.

## Tweets for X (owner posts them by hand)

The owner has no paid X API, so he copies each tweet into X (@AbdulbariH2771) himself and schedules it there. The best stories posted to the channel also get one ready-to-copy tweet, sent to the owner's private chat in the same hourly run (rules below; earlier rule of one tweet per story replaced 2026-11-13).

**Growth pattern (owner's request 2026-11-13, after comparing the account with Genki_JPN, NikTek, Pirat_Nation, Wario64 and Dexerto):** fewer, stronger tweets, each with an image. The channel still gets every story; X only gets the best ones.

**Which stories get a tweet** — in each hourly run, after the channel jobs, pick **at most ONE** story for X, and only if all of these hold:
- it is 09:00–23:59 Istanbul time;
- fewer than **6** tweets are logged in `tweets.txt` for today (Istanbul date);
- the last line of `tweets.txt` is at least **2 hours** old;
- the story has a usable image (a real article image, not a logo or a tiny thumbnail) — no image, no tweet;
- it is a **big** story: GTA 6 / Rockstar, Nintendo / PlayStation / Xbox / Steam platform news, a major release, reveal, trailer or delay, a big studio or industry move (CEO change, layoffs, acquisition, closure), a striking number (sales, price, players), a big deal or price change on consoles or GPUs, or a major esports result (Major / final). Small patches, minor indie news, minor sales and routine esports matches stay channel-only.
If several stories qualify, take the biggest (the one most people will talk about). Stories that do not get a tweet are **not** caught up later.

For the chosen story:

1. Together with the channel job, queue a second `sendPhoto` job to the owner's private chat (`state.json → telegram_chat_id`) with the same image, `--ref tweet-<slug>`, a `--fallback-text` with the same caption, and this caption (`parse_mode` HTML):

   ```
   <code>TWEET TEXT</code>
   ```
   The caption is **only** the `<code>` block — no header or "tap to copy" line before or after it (owner's request 2026-11-11). The owner posts the tweet **with this image attached**.

   TWEET TEXT is English, ideally **≤ 220 characters** (hard limit 270), and contains **no link** (the owner puts the link in the first reply — owner's request 2026-11-11 19:32), in your own words, only facts the source states. Escape `&`, `<`, `>`. Style = short, fact-first news (like Genki_JPN / Pirat_Nation):
   - **Line 1 = the fact itself**, under ~80 characters, with the number, price, date or big name up front, e.g. "🚨 Ocarina of Time remake: 2 in 3 copies sold in Japan are physical". One emoji at the start (🚨 big/breaking, 🎮 game, 🔥 hype, 💰 price/deal, 🖥️ hardware, 🏆 esports). No vague openers ("News:", "Check this out", "Yes, really").
   - Line 2: one short sentence with the key detail that makes it interesting.
   - A short question only on about **one tweet in three**, and only when it invites real opinions ("Day-one buy or wait?").
   - Then `via @Source` (from `handles.txt`; one source, two only if they fit) and **0–2 mentions** of the official accounts the story is about, as plain `@Handle` — only handles from `handles.txt` or confirmed by a web search, never guessed (owner's request 2026-11-12).
   - Then **2 hashtags** at most (the game or company + `#GamingNews` when it fits).
   - Shorten line 2 rather than drop the source or mentions. Vary openers; never the same pattern twice in a row.
   Right after it, queue a `sendMessage` job to the same private chat, `--ref tweetlink-<slug>`, `parse_mode` HTML, whose text is **only** `<code>SOURCE LINK</code>` (no label) — the owner copies it into the first reply under his tweet.
2. Queue the tweet jobs (photo + link message) **after** all the channel jobs, in the same push, and `tg.py wait` them too.
3. If the tweet job **and** the link job `wait` report ok, append `time GMT+3<TAB>link` to `tweets.txt` (commit it with `posted.txt`). If either failed, retry that story's tweet in the next run (it still counts against the limits above).

No tweet is sent for a story that was not posted to the channel, and never two tweets for the same story.

## Blogger — STOPPED

The owner asked on 2026-11-11 to stop posting to his blog (the emails were treated as spam). Do not send any email and do not use the Gmail tools. `blogged.txt` is kept only as history.
