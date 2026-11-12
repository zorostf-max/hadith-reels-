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

The owner has no paid X API, so he copies each tweet into X (@AbdulbariH2771) himself and schedules it there. **Every story posted to the channel also gets one ready-to-copy tweet, sent to the owner's private chat in the same hourly run** (owner's request 2026-11-09 23:29; this replaces the earlier "one tweet at 10:15 / 13:15 / 16:15 / 20:00" tasks, which are disabled).

In the hourly run, for each story chosen in step 3:

1. Together with the channel job, queue a second `sendPhoto` job to the owner's private chat (`state.json → telegram_chat_id`) with the same image, `--ref tweet-<slug>`, a `--fallback-text` with the same caption, and this caption (`parse_mode` HTML):

   ```
   <code>TWEET TEXT</code>
   ```
   The caption is **only** the `<code>` block — no header or "tap to copy" line before or after it (owner's request 2026-11-11).

   TWEET TEXT is English, **≤ 270 characters**, and contains **no link** (X shows link posts to fewer people; the owner puts the link in the first reply — owner's request 2026-11-11 19:32), in your own words, only facts the source states. Escape `&`, `<`, `>`. Write it to win views and follows (owner's request 2026-11-11):
   - **Line 1 = the hook**, under ~70 characters: start with an emoji that fits (🚨 big/breaking, 🎮 game, 🔥 hype, 💰 price/deal, 🖥️ hardware, 🏆 esports) and lead with the most surprising fact — a number, a date, a price, a big name. Never a vague opener like "News:" or "Check this out".
   - Line 2 (after a line break): one short sentence with the key detail (what / when / how much).
   - Line 3, about every other tweet: a short question that invites replies ("Day-one buy or wait?", "Worth $70?").
   - Then the **source**: `via @Source` — the source site's X account from `handles.txt` (e.g. `via @GameSpot`); with several sources, name the main one, or two if they fit (owner's request 2026-11-12).
   - Then **1–2 mentions** of the official X accounts the story is about, written as plain `@Handle` (real mentions on X — owner's request 2026-11-12). Only handles from `handles.txt` or confirmed by a web search, never guessed; none if no official account fits. Put them in the sentence where natural or on the same line as the source.
   - Then **2–3 hashtags** (the game, the company or platform, and `#GamingNews` when it fits).
   - The whole tweet stays **≤ 270 characters** — shorten line 2 rather than drop the source, mentions or hashtags.
   - Vary the openers and questions; never the same pattern twice in a row.
   Right after it, queue a `sendMessage` job to the same private chat, `--ref tweetlink-<slug>`, `parse_mode` HTML, whose text is **only** `<code>SOURCE LINK</code>` (no label) — the owner copies it into the first reply under his tweet.
2. Queue the tweet jobs (photo + link message) **after** all the channel jobs, in the same push, and `tg.py wait` them too.
3. For each story whose tweet job **and** link job `wait` reports as ok, append `time GMT+3<TAB>link` to `tweets.txt` (commit it with `posted.txt`).
4. Catch-up: before choosing news, any link in `posted.txt` from the last 24 hours (not a `(same story)` line) that is missing from `tweets.txt` also gets its tweet in this run (image from `fetch_news.py --hours 24 --limit 80 --include-posted`, or a plain `sendMessage` if there is no image), followed by its link message.

No tweet is sent for a story that was not posted to the channel, and never two tweets for the same story.

## Blogger — STOPPED

The owner asked on 2026-11-11 to stop posting to his blog (the emails were treated as spam). Do not send any email and do not use the Gmail tools. `blogged.txt` is kept only as history.
