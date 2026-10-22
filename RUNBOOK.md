# Keith weekly content runbook

Owner: Achal (Social Media Content Coordinator, Sociallyin). Account: Instagram @keithsol, Metricool blogId 7591743, timezone America/New_York.
This file is the instruction set for the weekly Tuesday run. Follow it end to end.

## What one run produces
1. ONE 8-slide carousel, scheduled for the coming THURSDAY at 6:30 PM ET, auto-publish.
2. SEVEN daily stories, Thursday through the following Wednesday, each at 12:00 PM ET.
   Default order (Thu to Wed): quick take or stat, POLL, news, quick take, POLL, news, my take.
   POLL stories are saved as Metricool DRAFTS (not scheduled). Achal posts them by hand from Instagram with the poll sticker.
   All other stories are scheduled with auto-publish.
Run on Tuesday morning so everything is queued 40+ hours before it goes live. Achal reviews in Metricool and deletes anything he dislikes.

## Hard rules
- Never publish immediately. Never schedule a time in the past. Instagram @keithsol only.
- No emoji. No em dashes (use commas or periods). Concise, confident, warm. Sociallyin tagline "Are you in?" is allowed.
- Facts: every claim comes from a primary or reputable source dated within the last 14 days. Open the source and confirm each number and date. If you cannot verify it, drop it. Never invent stats, quotes or screenshots. Source lines show the real publisher and real date. Do not write "this week" or "today" for items older than 7 days; the cover label should say "worth knowing right now" when items are older.
- Do not repeat topics from earlier weeks (see earlier week-*/spec.json in this repo).
- Screenshots must be real pages (the platform's own announcement or the publisher's graphic), captured through Claude in Chrome on Achal's Mac. Decline cookie banners, close popups. NEVER solve or bypass CAPTCHAs or bot checks: if a page blocks you, skip that source. Keep the cursor out of the frame (hover elsewhere before capturing). Never fake UI.
- If no real screenshot can be captured for a news item, use the "stat" slide type for the carousel, or a "quick" story, instead of an image.
- Slides are designed templates, not AI imagery, so isAiGenerated is false. If you ever add AI-generated imagery, set it true.
- Do not delete Metricool posts unless they are posts from THIS run that you are replacing.
- Do not post anything to Instagram Stories that needs the poll sticker. Polls are drafts only.

## Steps
1. Setup. Call add_repo for achal5/keith-content-assets with push access, then `git clone --depth 1 https://github.com/achal5/keith-content-assets /home/claude/keith-content-assets`. Then `cd pipeline && npm install`. Use the current_time tool for today's date (America/New_York).
2. Research. Find the 5 most useful AI + social media updates from the last 14 days for brands and creators (Instagram, Meta, Google, ChatGPT, TikTok, LinkedIn, YouTube). Open each source and extract exact figures and dates.
3. Screenshots. For each news item open the source in Chrome, dismiss banners, scroll to the graphic or section, capture with the zoom action (save_to_disk, region), crop with PIL if needed, save to week-YYYY-MM-DD/img/.
4. Write week-YYYY-MM-DD/spec.json (named for the Thursday carousel date). Copy the format from pipeline/examples/week-2026-10-22.json. Types:
   - carousel.cover {hook, label, date}; carousel.slides[] of "stat" {tag, number, headline, sub, source} or "news" {tag, headline, sub, image, fit "cover"|"contain", image_bg, image_h 380|430, icon, source}; carousel.take {headline, sub}; carousel.cta {headline, sub, keyword}.
   - icons: clock carousel link trend chat search bolt users play megaphone.
   - Put [[double brackets]] around the highlighted words in headlines.
   - stories[]: "quick" {name, chip, number?, headline, sub, source?, size?}, "news" {name, chip, headline, image, fit, image_bg, sub, source}, "poll" {name, headline, context}.
   - name each story file story-thu, story-fri, story-sat, story-sun, story-mon, story-tue, story-wed.
   Carousel slide order: cover, stat, then 4 news slides, take, cta (8 total). Keep copy short enough to avoid overflow.
5. Build: `python3 pipeline/build.py week-YYYY-MM-DD/spec.json week-YYYY-MM-DD`. Open EVERY PNG with Read and check for clipping, overflow, typos and wrong numbers. Fix the spec and rebuild until clean.
6. Push the week folder to main (spec, PNGs, img). Check that every raw URL returns HTTP 200: https://raw.githubusercontent.com/achal5/keith-content-assets/main/week-YYYY-MM-DD/<file>. If you re-push a changed file, use a new filename (raw URLs are cached).
7. Metricool (createScheduledPost, blogId 7591743):
   - Carousel: info = {"draft": false, "autoPublish": true, "text": <caption>, "media": [8 raw URLs in order], "mediaAltText": [], "providers": [{"network":"instagram"}], "publicationDate": {"dateTime":"YYYY-MM-DDT18:30:00","timezone":"America/New_York"}, "instagramData": {"type":"POST","isAiGenerated":false}, "firstCommentText":"", "hasNotReadNotes": false, "shortener": false, "descendants": [], "smartLinkData": {"ids":[]}}. date param = same time with -04:00 or -05:00 offset as correct for that date.
   - Caption: hook line, blank line, "Five updates:" then numbered one-line items, blank line, "My take: ...", blank line, CTA line, blank line, 3 to 5 hashtags. No emoji.
   - Story (auto-publish): info = {"draft": false, "autoPublish": true, "media": [raw URL], "mediaAltText": [short description], "providers": [{"network":"instagram"}], "publicationDate": {...T12:00:00 America/New_York}, "instagramData": {"type":"STORY","isAiGenerated":false}, "firstCommentText":"", "hasNotReadNotes": false, "shortener": false, "descendants": [], "smartLinkData": {"ids":[]}, "text": ""}.
   - Poll story: same but "draft": true and "autoPublish": false.
8. Tidy the repo: git rm week-* folders older than 21 days (keep pipeline/ and this runbook), commit and push.
9. Final report (this is what Achal reads; also sent by push + email): list every scheduled item with day, time and one-line description; list the poll stories with the day to post and the two sticker answers, and send the poll PNGs with SendUserFile; list the sources used with links; say plainly what was dropped, could not be verified, or could not be screenshotted. Include the Metricool planner link. Remind him he can delete anything in the Metricool planner before it goes live.
If a step fails, still report exactly what is and is not scheduled. Never leave a half-scheduled week without saying so.

## Commit messages
End commit messages with the Co-Authored-By and Claude-Session lines given in the session instructions.

## Notes
- The first automated run is Tuesday Oct 27, 2026: carousel Thu Oct 29, stories Thu Oct 29 to Wed Nov 4. Stories for Oct 22 to Oct 28 were scheduled by hand.
- The cover and carousel promise "Comment UPDATE and I'll send you the full list". Achal sends the list manually; keep this CTA unless told otherwise.
- Audio: auto-published carousels and stories cannot carry trending audio.
