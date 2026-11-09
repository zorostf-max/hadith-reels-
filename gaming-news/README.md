# Level Up — gaming news for Telegram

Automatic gaming news for the owner's Telegram channel **Level up** (`@LevelUpGames0`, chat id `-1003872817226`), posted by the bot `@my_cs2_monitor_bot` through the **GitHub Actions Telegram bridge** (`telegram/README.md`) — not AnythingMCP.
This folder is separate from the hadith reels project in the rest of the repo — never touch the hadith files, `state.json` or the hadith Telegram approval flow from here.

Owner's rules (2026-11-09):
- Post **each news item on its own, soon after it comes out** (a scheduled run every hour).
- Post **directly** to the channel, no approval step.
- Write in **English**, always with the **source** linked and the item's **publish time**.
- Topics: game news and releases · esports and tournaments (CS2, Valorant, LoL…) · PC hardware and graphics cards · platforms and deals (PlayStation, Xbox, Nintendo, Steam, free games, big discounts).

Files: `fetch_news.py` (reads the RSS feeds, prints fresh items as JSON with an image URL) · `posted.txt` (log of every link already posted or skipped as a duplicate — one line per link: `time<TAB>source<TAB>url`).

## RUNBOOK — hourly run

1. `cd` into the repo, `git pull`. `pip install --break-system-packages -q feedparser` if it is missing.
2. `python3 gaming-news/fetch_news.py --hours 2 --limit 30`. It already drops links in `posted.txt`.
3. Choose what to post (**at most 4 posts per run**, oldest first):
   - **Keep** real news in the four topics above.
   - **Skip**: walkthroughs/guides ("how to find…", "all locations…"), redeem-code lists, quizzes and NYT puzzle answers, opinion/review pieces with no news, non-gaming stories (food, animals, general politics, film/TV unless it is a game adaptation), small affiliate deals. Do not log skipped items; they age out of the 2-hour window on their own.
   - **One story = one post.** If several sources cover the same story (in this run or already in `posted.txt` from the last day), post it once and log the other links as `(same story)`.
   - If nothing qualifies, stop without posting (log nothing, no commit needed).
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
6. For each job that `wait` reports as ok, append its line to `posted.txt` (time in GMT+3, source, link). Then `git add gaming-news && git commit -m "news: N posts" && git push` (pull --rebase and retry once if the push is rejected).
7. If a feed in `feed_errors` keeps failing, or the bot cannot post (e.g. it lost admin rights), queue one short `sendMessage` to the owner (`state.json` → `telegram_chat_id`) — at most once a day.
