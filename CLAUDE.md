# State of the Church Today — repo rules

Weekly curated digest of Southern Baptist, Reformed, and broader theological news for pastors and elders. Owner: Justin Rolston (Reformed Baptist; Maranatha Community Church elder). Published at https://churchnews.therolstons.com via GitHub Pages from `docs/`.

## Layout

- `issues/YYYY-MM-DD-issue-NN.md` — source of truth. One file per issue. Never edit past issues except to fix a factual error (note the correction at the bottom).
- `scripts/build.py` — renders `docs/` (HTML, MP3 via edge-tts, `feed.xml`, `issues.json`). Run after writing an issue. Do not hand-edit `docs/`.
- `docs/audio/*.txt` — the exact script read aloud; check it if audio sounds wrong.

## Weekly job (Sundays)

1. Issue number = highest NN in `issues/` + 1. Date = today.
2. Research (below). Write `issues/YYYY-MM-DD-issue-NN.md` using the format in any prior issue — same frontmatter, masthead, italic lede in a `>` blockquote, five beats with the emoji `##` headers (⛪ 📖 🕊️ 🏛️ 🔥), each item as `**Headline.** text — [Source](URL)`, then `## 🧭 For the Elder's Desk` with one `>` paragraph, then the compiled-on footer line.
3. `pip install -q markdown python-frontmatter edge-tts mutagen && python scripts/build.py`
4. `git add -A && git commit -m "Issue NN — YYYY-MM-DD" && git push`
5. Report: 2–3 sentence summary of lead stories, any beat with no real news, and any source checked that yielded nothing usable.

## Research

Prefer items from the last 7–10 days. Beats: SBC & Convention Watch · Reformed & Confessional · Theology & Doctrine · Culture & Church-State · Also Worth Noting. 1–5 items per beat; omit a beat if nothing is newsworthy. Each item: what happened, why it matters to a pastor/elder, what to watch. Curated-digest tone — brief, sourced, discerning, never sensational. Pastoral matters handled with gravity; "reported with discernment, not appetite."

Check these directly every week, not just via keyword search:
- WORLD (wng.org) — best for Culture & Church-State. Gated; write only from what's visible.
- Founders (founders.org) and Grimké Seminary (grimkeseminary.org) — announcements, articles, conferences. Frame as announcements, not news.

Sourcing lessons (keep updating):
- Baptist Press's own site returns stale results in search and fetches empty. **The Missouri Pathway (mbcpathway.com) republishes BP with clean dates — use it as the primary SBC source.** Also Biblical Recorder (brnow.org), Baptist Standard, The Baptist Paper.
- RNS (religionnews.com) fetches cleanly and dates reliably; good for ACNA, aid/politics, scandals.
- Heidelblog dates in URL path; Founders homepage shows latest podcast/articles.
- Always verify the year on anything from search — Iorg reorg, EC motions, Wyoming, LSU shooting all surfaced as "current" and were years old.

## Verification before commit

- Every URL must come from an actual search result or fetched page. Never invent or guess URLs.
- Confirm dates, names, and that stories are genuinely recent. Soften or drop shaky claims.
- Prefer a news report over an organization's own page; if only the org's page exists, call it an announcement.
