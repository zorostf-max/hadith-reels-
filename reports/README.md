# Weekly growth report (owner's request 2026-11-13)

Every **Sunday ~20:41 Istanbul** a scheduled run sends the owner ONE Arabic Telegram message (through the GitHub bridge, `telegram/README.md`; chat `state.json → telegram_chat_id`) with the week's numbers for the Islamic accounts and what to change. It only reads and reports: it never publishes, schedules, edits or deletes anything.

## Data (last 7 days, Monday–Sunday)

- **Instagram (@hadithdaily.bukhari) and YouTube (Hadith Daily):** Metricool `getAnalyticsDataByMetrics`, brandId `state.json → metricool_blog_id`. Instagram reels: `IGRE02` date, `IGRE03` text, `IGRE23` views, `IGRE11` reach, `IGRE10` likes, `IGRE07` comments, `IGRE21` shares, `IGRE12` saves, `IGRE24` avg watch time, `IGRE30` skip rate. YouTube: connector "videos published in range" (`YTVP02` date, `YTVP17` title, `YTVP06` views, `YTVP08` avg view duration, `YTVP09` likes, `YTVP11` comments). If a metric comes back empty, say «لا تتوفر بيانات» for it — never estimate.
- **TikTok (@hadithdaily.bukhari):** vidIQ `vidiq_tiktok_profile` (followers, total likes) and `vidiq_tiktok_profile_videos` (views/likes/comments/shares per video).
- **Previous week:** `reports/history.json` (append this week's totals at the end of the run: date, followers/subscribers per platform, total views per platform). Compare with last week (▲/▼ and the difference).
- **Goals:** TikTok 1,000 followers by end of 2026-12 (unlocks bio link and LIVE); show progress as «X / 1000».

## Message (Arabic, ≤ 3,500 characters; split if longer)

```
📊 تقرير الأسبوع (<من> – <إلى>)

🎵 تيك توك: <متابعون> (▲/▼ <فرق>) · مشاهدات الأسبوع <مجموع> · هدف ١٠٠٠: <X>/1000
▶️ يوتيوب: <مشتركون إن توفروا> · مشاهدات الأسبوع <مجموع>
📸 إنستغرام: مشاهدات الأسبوع <مجموع> · نسبة التخطي في أول ٣ ثوانٍ <متوسط>٪

🏆 أفضل ٣ فيديوهات (كل المنصات): العنوان — المنصة — المشاهدات
⚠️ أضعف فيديو: …

💡 ماذا نتعلّم:
• <ملاحظة واحدة مبنية على الأرقام: أي سلسلة/نوع عنوان/مدة نجح أكثر>
• <ملاحظة ثانية>

✅ اقتراح للأسبوع القادم: <اقتراح واحد محدد قابل للتنفيذ>
```

Base every sentence on the numbers you fetched; if a platform's data failed, say so in one line and continue with the others.
