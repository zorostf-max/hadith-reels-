# Level Up — gaming news for Telegram

Automatic gaming news for the owner's Telegram channel **Level up** (`@LevelUpGames0`, chat id `-1003872817226`), posted by the bot `@my_cs2_monitor_bot` through the **GitHub Actions Telegram bridge** (`telegram/README.md`) — not AnythingMCP.
This folder is separate from the hadith reels project in the rest of the repo — never touch the hadith files, `state.json` or the hadith Telegram approval flow from here.

Owner's rules (2026-11-09):
- Post **each news item on its own, soon after it comes out** (a scheduled run every hour).
- Post **directly** to the channel, no approval step.
- Write in **English**, always with the **source** linked and the item's **publish time**.
- Topics: game news and releases · esports and tournaments (CS2, Valorant, LoL…) · PC hardware and graphics cards · platforms and deals (PlayStation, Xbox, Nintendo, Steam, free games, big discounts).

Files: `tweets.txt` (log of links whose tweet was sent to the owner) · `fetch_news.py` (reads the RSS feeds, prints fresh items as JSON with an image URL) · `posted.txt` (log of every link already posted or skipped as a duplicate — one line per link: `time<TAB>source<TAB>url`).

## RUNBOOK — hourly run

1. `cd` into the repo, `git pull`. `pip install --break-system-packages -q feedparser` if it is missing.
2. `python3 gaming-news/fetch_news.py --hours 2 --limit 30`. It already drops links in `posted.txt`.
3. Choose what to post (**at most 4 posts per run**, oldest first):
   - **Keep** real news in the four topics above.
   - **Skip**: walkthroughs/guides ("how to find…", "all locations…"), redeem-code lists, quizzes and NYT puzzle answers, opinion/review pieces with no news, non-gaming stories (food, animals, general politics, film/TV unless it is a game adaptation), small affiliate deals. Do not log skipped items; they age out of the 2-hour window on their own.
   - **One story = one post.** If several sources cover the same story (in this run or already in `posted.txt` from the last day), post it once and log the other links as `(same story)`.
   - If nothing qualifies, post nothing, but still push the tick job of step 6.
4. For each chosen item, if the RSS summary is too thin to write two accurate sentences, read the article with WebFetch. Write only facts the source states; never invent numbers, dates or quotes.
5. For each item queue a `sendPhoto` job (`python3 telegram/tg.py queue sendPhoto '{"chat_id":"@LevelUpGames0","photo":"<image>","parse_mode":"HTML","caption":"…"}' --ref news-<slug> --fallback-text "<same caption>"`), then commit + push once and run `python3 telegram/tg.py wait <all job names>`. Caption (≤ 1024 chars) in this shape — own words, no copied sentences, at most one short quote under 15 words:

   ```
   <emoji> <b>Headline in my own words</b>

   2–3 short sentences: what happened, the key detail, why it matters.

   🕒 Nov 9, 2026 · 17:32 (GMT+3)
   📰 Source: <a href="LINK">Source name</a>

   #Tag1 #Tag2 #GamingNews
   ```
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

   TWEET TEXT is English, **≤ 270 characters including the link** (X counts any link as 23), in your own words, only facts the source states. Escape `&`, `<`, `>`. Write it to win views and follows (owner's request 2026-11-11):
   - **Line 1 = the hook**, under ~70 characters: start with an emoji that fits (🚨 big/breaking, 🎮 game, 🔥 hype, 💰 price/deal, 🖥️ hardware, 🏆 esports) and lead with the most surprising fact — a number, a date, a price, a big name. Never a vague opener like "News:" or "Check this out".
   - Line 2 (after a line break): one short sentence with the key detail (what / when / how much).
   - Line 3, about every other tweet: a short question that invites replies ("Day-one buy or wait?", "Worth $70?").
   - Then the source link, then 1–2 relevant hashtags (game name or platform, e.g. #GTA6 #PS5) — never more than 2.
   - Vary the openers and questions; never the same pattern twice in a row.
2. Queue the tweet jobs **after** all the channel jobs, in the same push, and `tg.py wait` them too.
3. For each tweet job that `wait` reports as ok, append `time GMT+3<TAB>link` to `tweets.txt` (commit it with `posted.txt`).
4. Catch-up: before choosing news, any link in `posted.txt` from the last 24 hours (not a `(same story)` line) that is missing from `tweets.txt` also gets its tweet in this run (image from `fetch_news.py --hours 24 --limit 80 --include-posted`, or a plain `sendMessage` if there is no image).

No tweet is sent for a story that was not posted to the channel, and never two tweets for the same story.

## Blogger — byte-beyondtech.blogspot.com (owner's request 2026-11-10)

Every story posted to the channel is **also published on the owner's blog** `byte-beyondtech.blogspot.com`, in the same hourly run, through Blogger's "post by email" (published immediately). The secret posting address is **only in the scheduled task's prompt — never write it in this public repo** (anyone who knows it can post to the blog).

**At most ONE blog post per hourly run** (2026-11-10: Blogger accepted the first email of each run and blocked the rest with 5.7.0, so it rate-limits post-by-email). Pick the single most important story of the run that is not yet in `blogged.txt`; if the run posted nothing new, take the newest channel story of the last 6 hours missing from `blogged.txt`.

For that story:

1. Send ONE email with the Gmail tool `send_message`, from the owner's Gmail, to the posting address in the task prompt:
   - `subject` = the headline (plain text, no emoji, no HTML) — it becomes the post title.
   - `htmlBody`, English, own words, only facts the source states:
     ```
     <p>Lead paragraph: what happened (2–3 sentences).</p>
     <p>Second paragraph: the key details and why it matters (2–4 sentences). Read the article with WebFetch if the RSS summary is thin.</p>
     <p>🕒 Nov 10, 2026 · 13:32 (GMT+3)<br>📰 Source: <a href="LINK">Source name</a></p>
     <p>Follow Level Up on Telegram: <a href="https://t.me/LevelUpGames0">@LevelUpGames0</a></p>
     ```
   - No images (Gmail strips external images from the body), no signature.
2. After it sends, append `time GMT+3<TAB>link` to `gaming-news/blogged.txt` and commit it with `posted.txt`.
3. Never two blog posts for one story; no blog post for a story that was not posted to the channel. If Gmail refuses, skip the blog for this run (no retry loop) and mention it in the run summary.
