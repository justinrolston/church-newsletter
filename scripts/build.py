#!/usr/bin/env python3
"""
Build State of the Church Today site from issues/*.md

  issues/YYYY-MM-DD-issue-NN.md  ->  docs/issues/YYYY-MM-DD-issue-NN.html
                                     docs/audio/YYYY-MM-DD-issue-NN.mp3   (edge-tts)
                                     docs/index.html, docs/feed.xml, docs/issues.json

Usage:
  python scripts/build.py            # build everything, skip existing mp3s
  python scripts/build.py --no-audio # html/feed only
  python scripts/build.py --force    # regenerate audio too

Deps: pip install markdown python-frontmatter edge-tts mutagen
"""
import argparse, asyncio, datetime as dt, email.utils, html, json, os, re, subprocess, sys
from pathlib import Path

import frontmatter, markdown

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
DOCS = ROOT / "docs"
SITE = "https://churchnews.therolstons.com"
TITLE = "State of the Church Today"
TAGLINE = "A weekly digest of Southern Baptist, Reformed, and broader theological news — curated for pastors and elders."
VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")

CSS = """
:root{color-scheme:light dark;
--bg:#f6f7f7;--ink:#171d1c;--muted:#5d6866;--rule:#d8dedc;--panel:#ffffff;--accent:#1d5a86;--accent-ink:#ffffff;
--b1:#1d5a86;--b2:#2a7f6f;--b3:#6b4f9e;--b4:#b3552b;--b5:#5f6b73}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121716;--ink:#e5e9e8;--muted:#97a19e;--rule:#29312f;--panel:#1a201f;--accent:#7db8dc;--accent-ink:#0f1b24;
--b1:#7db8dc;--b2:#6fc2b0;--b3:#b39ddb;--b4:#e39068;--b5:#9aa7ae;color-scheme:dark}}
:root[data-theme=dark]{--bg:#121716;--ink:#e5e9e8;--muted:#97a19e;--rule:#29312f;--panel:#1a201f;--accent:#7db8dc;--accent-ink:#0f1b24;
--b1:#7db8dc;--b2:#6fc2b0;--b3:#b39ddb;--b4:#e39068;--b5:#9aa7ae;color-scheme:dark}
:root[data-theme=light]{color-scheme:light}
*{box-sizing:border-box}
html{font-size:17px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Instrument Sans",system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--accent)}
a:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
.wrap{max-width:660px;margin:0 auto;padding:0 22px 72px;overflow-wrap:anywhere}
header.masthead{display:flex;align-items:baseline;justify-content:space-between;gap:16px;padding:26px 0 14px;border-bottom:1px solid var(--rule)}
header.masthead .wordmark{font-weight:700;font-size:1rem;letter-spacing:-.01em;color:var(--ink);text-decoration:none}
header.masthead .wordmark:hover{color:var(--accent)}
header.masthead nav{font-size:.85rem;display:flex;gap:18px;align-items:center}
.theme{appearance:none;border:1px solid var(--rule);background:var(--panel);color:var(--muted);width:30px;height:30px;border-radius:50%;padding:0;display:grid;place-items:center;cursor:pointer}
.theme:hover{color:var(--accent);border-color:var(--accent)}
.theme svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.theme .moon{display:none}
:root[data-theme=dark] .theme .sun{display:none}:root[data-theme=dark] .theme .moon{display:block}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]) .theme .sun{display:none}:root:not([data-theme=light]) .theme .moon{display:block}}
header.masthead nav a{color:var(--muted);text-decoration:none}
header.masthead nav a:hover{color:var(--accent)}
.issuehead{padding:44px 0 8px}
.issuehead .date{font-size:.9rem;color:var(--muted);margin:0 0 10px}
.issuehead .date b{color:var(--ink);font-weight:600}
h1.title{font-size:2.15rem;line-height:1.12;letter-spacing:-.02em;font-weight:700;margin:0}
.body>blockquote:first-of-type{border:0;background:none;padding:0;margin:18px 0 6px;font-size:1.22rem;line-height:1.45;color:var(--ink)}
.body>blockquote:first-of-type p{margin:0}
.audio{display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 16px;align-items:center;margin:26px 0 6px;padding:16px 18px;background:var(--panel);border:1px solid var(--rule);border-radius:10px}
.audio .play{width:40px;height:40px;border-radius:50%;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;grid-row:span 2}
.audio .play svg{width:16px;height:16px;fill:currentColor;margin-left:2px}
.audio .lbl{font-weight:600;font-size:.95rem;line-height:1.2}
.audio .lbl span{color:var(--muted);font-weight:400;margin-left:6px}
.audio audio{width:100%;min-width:0;height:36px;grid-column:2}
.body hr{border:0;border-top:1px solid var(--rule);margin:36px 0 0}
.body h2{position:relative;font-size:1.05rem;font-weight:700;margin:34px 0 4px;padding-top:14px}
.body h2::before{content:"";position:absolute;top:0;left:0;width:34px;height:3px;border-radius:2px;background:var(--beat,var(--accent))}
.body h2.b1{--beat:var(--b1)}.body h2.b2{--beat:var(--b2)}.body h2.b3{--beat:var(--b3)}.body h2.b4{--beat:var(--b4)}.body h2.b5{--beat:var(--b5)}
.body h2+p em{font-style:normal;font-size:.9rem;color:var(--muted)}
.body h2+p{margin-bottom:14px}
.body p{margin:0 0 20px}
.body a{color:var(--accent);text-decoration:underline;text-decoration-color:color-mix(in srgb,var(--accent) 35%,transparent);text-underline-offset:3px}
.body a:hover{text-decoration-color:var(--accent)}
.body .src{font-size:.86rem;line-height:2}
.body .src a{color:var(--muted);text-decoration:none;border:1px solid var(--rule);border-radius:999px;padding:1px 9px;margin-left:4px;white-space:nowrap}
.body .src a:hover{color:var(--accent);border-color:var(--accent)}
.body .elder{margin:40px 0 0;padding:22px 24px 6px;border-left:3px solid var(--accent);background:var(--panel);border-radius:0 10px 10px 0}
.body .elder h2{margin-top:0;padding-top:0}
.body .elder h2::before{display:none}
.body .elder blockquote{margin:0 0 16px;padding:0;font-size:1.05rem;line-height:1.6}
.body .elder blockquote p{margin:0 0 14px}
.body>p:last-child em{font-style:normal;font-size:.86rem;color:var(--muted)}
footer.foot{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:.86rem;color:var(--muted);margin-top:56px;padding-top:18px;border-top:1px solid var(--rule);line-height:1.6}
footer.foot a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--rule)}
footer.foot a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.index-intro{padding:44px 0 10px}
.index-intro h1{font-size:2.15rem;line-height:1.12;letter-spacing:-.02em;margin:0 0 10px}
.index-intro p{margin:0;color:var(--muted);font-size:1.05rem;max-width:34em}
ul.issues{list-style:none;padding:0;margin:26px 0 0}
ul.issues li{display:grid;grid-template-columns:110px minmax(0,1fr);gap:4px 20px;padding:20px 0;border-top:1px solid var(--rule)}
ul.issues .d{font-size:.86rem;color:var(--muted);line-height:1.5;padding-top:3px}
ul.issues .d b{display:block;color:var(--ink);font-weight:600}
ul.issues .lede{margin:0;line-height:1.5}
ul.issues .lede a{color:var(--ink);text-decoration:none}
ul.issues .lede a:hover{color:var(--accent)}
ul.issues .links{grid-column:2;font-size:.86rem;margin-top:8px;display:flex;gap:14px}
ul.issues .links a{color:var(--accent);text-decoration:none}
ul.issues .links a:hover{text-decoration:underline}
@media(max-width:540px){html{font-size:16px}h1.title,.index-intro h1{font-size:1.75rem}ul.issues li{grid-template-columns:1fr}ul.issues .lede,ul.issues .links{grid-column:1}header.masthead{flex-direction:column;gap:6px;align-items:flex-start}}
@media(prefers-reduced-motion:no-preference){.body a,ul.issues a,header a{transition:color .15s}}
"""

def page(title, body, extra_head=""):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(TAGLINE)}">
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="{SITE}/feed.xml">
<link rel="icon" href="{SITE}/favicon.svg" type="image/svg+xml">{extra_head}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">
<style>{CSS}</style>
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script></head><body><div class="wrap">
<header class="masthead"><a class="wordmark" href="{SITE}/">{TITLE}</a>
<nav><a href="{SITE}/issues/">All issues</a><a href="{SITE}/feed.xml">Podcast feed</a>
<button class="theme" type="button" aria-label="Switch between light and dark mode" title="Light or dark mode">{SUN_SVG}{MOON_SVG}</button></nav></header>
{body}
<footer class="foot"><span>New issues every Sunday morning. Corrections and tips welcome.</span><span>Powered by <a href="https://bishop.therolstons.com/">the Bishop</a></span></footer>
</div>
<script>document.querySelector(".theme").addEventListener("click",function(){{var r=document.documentElement,d=r.dataset.theme||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light"),n=d==="dark"?"light":"dark";r.dataset.theme=n;try{{localStorage.setItem("theme",n)}}catch(e){{}}}});</script>
</body></html>"""

def load_issues():
    out = []
    for p in sorted(ISSUES.glob("*-issue-*.md")):
        post = frontmatter.load(p)
        slug = p.stem
        body = post.content
        # strip the duplicate masthead lines from the md (title, tagline, issue line)
        body = re.sub(r"^# State of the Church Today\s*\n", "", body, flags=re.M)
        body = re.sub(r"^\*A weekly digest of .*?\*\s*\n", "", body, flags=re.M)
        body = re.sub(r"^\*\*Issue \d+ · .*?\*\*\s*\n", "", body, flags=re.M)
        lede = ""
        m = re.search(r"^> (.+)$", body, flags=re.M)
        if m: lede = m.group(1).strip()
        d = post.get("date")
        if isinstance(d, str): d = dt.date.fromisoformat(d)
        out.append(dict(slug=slug, path=p, meta=post.metadata, body=body, lede=lede,
                        date=d, issue=int(post.get("issue", 0)),
                        title=post.get("title", f"{TITLE} — Issue {post.get('issue')}")))
    return sorted(out, key=lambda i: (i["date"], i["issue"]))

BEATS = [("SBC", "b1"), ("Reformed", "b2"), ("Theology", "b3"), ("Culture", "b4"), ("Also", "b5")]
SUN_SVG = '<svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
MOON_SVG = '<svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1d5a86"/>'
           '<g fill="#fff"><rect x="30" y="8" width="4" height="14"/><rect x="25" y="12" width="14" height="4"/>'
           '<path d="M32 20 L44 30 L44 52 L20 52 L20 30 Z"/><path d="M14 36 L20 31 L20 52 L14 52 Z"/><path d="M50 36 L44 31 L44 52 L50 52 Z"/></g>'
           '<rect x="29" y="40" width="6" height="12" fill="#1d5a86"/></svg>')
PLAY_SVG = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 1.5v13l11-6.5z"/></svg>'

def beat_class(text):
    for key, cls in BEATS:
        if key.lower() in text.lower(): return cls
    return ""

def mp3_duration(path):
    try:
        from mutagen.mp3 import MP3
        return f"{int(MP3(path).info.length) // 60} min"
    except Exception:
        return ""

def short_title(t):
    return t.replace(TITLE + " — ", "")

def render_issue(i, has_audio, home=False):
    md = markdown.Markdown(extensions=["smarty"])
    body_html = md.convert(i["body"])
    # strip emoji from beat headers and tag each with its beat colour
    def fix_h2(m):
        text = re.sub(r"^[^\w(]+", "", m.group(1)).strip()
        cls = beat_class(text)
        return f'<h2 class="{cls}">{text}</h2>' if cls else f"<h2>{text}</h2>"
    body_html = re.sub(r"<h2>(.*?)</h2>", fix_h2, body_html)
    # "— [Source](url) · [Source](url)" tails become source tags
    LINK = r"<a [^>]+>[^<]+</a>"
    body_html = re.sub(r"\s*[—–-]\s*(" + LINK + r"(?:\s*·\s*" + LINK + r")*)\s*(?=</p>)",
                       lambda m: ' <span class="src">' + re.sub(r"\s*·\s*", " ", m.group(1)) + "</span>", body_html)
    # wrap the Elder's Desk section in the accented panel
    body_html = re.sub(r"(<h2[^>]*>For the Elder.*?)(?=<hr\s*/?>|<p><em>State of the Church Today)",
                       r'<div class="elder">\1</div>', body_html, flags=re.S)
    # drop the markdown sign-off line (and its rule); the page footer carries that
    body_html = re.sub(r"(<hr\s*/?>\s*)?<p><em>State of the Church Today\b.*?</em></p>\s*$", "", body_html, flags=re.S)
    head = (f'<div class="issuehead"><p class="date">{"Latest issue &nbsp; " if home else ""}{i["date"].strftime("%A, %B %-d, %Y")}</p>'
            f'<h1 class="title">{html.escape(short_title(i["title"]))}</h1></div>')
    audio = ""
    if has_audio:
        dur = mp3_duration(DOCS / "audio" / f"{i['slug']}.mp3")
        audio = (f'<div class="audio"><div class="play">{PLAY_SVG}</div><div class="lbl">Listen to this issue'
                 f'{"<span>" + dur + "</span>" if dur else ""}</div>'
                 f'<audio controls preload="none" src="{SITE}/audio/{i["slug"]}.mp3"></audio></div>')
    # lede first, then the player, then the rest
    lede_m = re.match(r"\s*(<blockquote>.*?</blockquote>)(.*)", body_html, flags=re.S)
    body_html = (lede_m.group(1) + audio + lede_m.group(2)) if lede_m else (audio + body_html)
    canon = f'<link rel="canonical" href="{SITE}/issues/{i["slug"]}.html">' if home else ""
    return page(TITLE if home else i["title"], f'{head}<div class="body">{body_html}</div>', extra_head=canon)

def render_index(issues, audio_slugs):
    items = []
    for i in reversed(issues):
        links = [f'<a href="{SITE}/issues/{i["slug"]}.html">Read</a>']
        if i["slug"] in audio_slugs: links.append(f'<a href="{SITE}/audio/{i["slug"]}.mp3">Listen</a>')
        links.append(f'<a href="{SITE}/issues/{i["slug"]}.md">Markdown</a>')
        items.append(f'<li><div class="d"><b>Issue {i["issue"]}</b>{i["date"].strftime("%b %-d, %Y")}</div>'
                     f'<p class="lede"><a href="{SITE}/issues/{i["slug"]}.html">{html.escape(i["lede"])}</a></p><div class="links">{"".join(links)}</div></li>')
    intro = f'<div class="index-intro"><h1>All issues</h1><p>{html.escape(TAGLINE)}</p></div>'
    return page(f"All issues — {TITLE}", intro + f'<ul class="issues">{"".join(items)}</ul>')

# ---------- audio ----------
def tts_script(i):
    t = i["body"]
    LINK = r"\[[^\]]+\]\([^)]+\)"
    t = re.sub(r"\s*—\s*" + LINK + r"(\s*·\s*" + LINK + r")*\s*$", "", t, flags=re.M)  # drop "— [Source](url) · [Source](url)" tails
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)            # remaining inline links -> text
    t = re.sub(r"^\*(.*?)\*\s*$", "", t, flags=re.M)           # italic beat subtitles / footer
    t = re.sub(r"^---\s*$", "", t, flags=re.M)
    t = re.sub(r"^## \S+\s+(.+)$", r"\n\nNext: \1.\n", t, flags=re.M)  # emoji headers -> spoken transitions
    t = re.sub(r"^> ", "", t, flags=re.M)
    t = re.sub(r"[*_`#>]", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    intro = f"{TITLE}. Issue {i['issue']}, {i['date'].strftime('%B %-d, %Y')}. {TAGLINE}\n\n"
    return intro + t + "\n\nThat's this week's State of the Church Today. New issues every Sunday morning."

async def make_audio(i, out: Path):
    import edge_tts
    text = tts_script(i)
    (DOCS / "audio" / f"{i['slug']}.txt").write_text(text)   # keep script for review
    com = edge_tts.Communicate(text, VOICE, rate="-5%")
    await com.save(str(out))

# ---------- feed ----------
def build_feed(issues, audio_slugs):
    from mutagen.mp3 import MP3
    items = []
    for i in reversed(issues):
        if i["slug"] not in audio_slugs: continue
        mp3 = DOCS / "audio" / f"{i['slug']}.mp3"
        size = mp3.stat().st_size
        dur = int(MP3(mp3).info.length)
        pub = email.utils.format_datetime(dt.datetime.combine(i["date"], dt.time(7, 0), tzinfo=dt.timezone(dt.timedelta(hours=-5))))
        items.append(f"""<item>
<title>{html.escape(i['title'])}</title>
<link>{SITE}/issues/{i['slug']}.html</link>
<guid isPermaLink="true">{SITE}/issues/{i['slug']}.html</guid>
<pubDate>{pub}</pubDate>
<description>{html.escape(i['lede'])}</description>
<enclosure url="{SITE}/audio/{i['slug']}.mp3" length="{size}" type="audio/mpeg"/>
<itunes:duration>{dur}</itunes:duration>
</item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>{TITLE}</title><link>{SITE}/</link><language>en-us</language>
<description>{html.escape(TAGLINE)}</description>
<itunes:author>Justin Rolston</itunes:author>
<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
{''.join(items)}
</channel></rss>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    (DOCS / "issues").mkdir(parents=True, exist_ok=True)
    (DOCS / "audio").mkdir(parents=True, exist_ok=True)
    issues = load_issues()

    audio_slugs = set()
    for i in issues:
        mp3 = DOCS / "audio" / f"{i['slug']}.mp3"
        if not a.no_audio and (a.force or not mp3.exists()):
            print("tts", i["slug"]); asyncio.run(make_audio(i, mp3))
        if mp3.exists(): audio_slugs.add(i["slug"])

    for i in issues:
        (DOCS / "issues" / f"{i['slug']}.html").write_text(render_issue(i, i["slug"] in audio_slugs))
        (DOCS / "issues" / f"{i['slug']}.md").write_text(i["path"].read_text())
    (DOCS / "issues" / "index.html").write_text(render_index(issues, audio_slugs))
    latest = issues[-1]
    (DOCS / "index.html").write_text(render_issue(latest, latest["slug"] in audio_slugs, home=True))
    (DOCS / "feed.xml").write_text(build_feed(issues, audio_slugs))
    (DOCS / "issues.json").write_text(json.dumps([{
        "issue": i["issue"], "date": i["date"].isoformat(), "title": i["title"], "lede": i["lede"],
        "html_url": f"{SITE}/issues/{i['slug']}.html", "md_url": f"{SITE}/issues/{i['slug']}.md",
        "mp3_url": f"{SITE}/audio/{i['slug']}.mp3" if i["slug"] in audio_slugs else None,
    } for i in reversed(issues)], indent=2))
    (DOCS / "favicon.svg").write_text(FAVICON)
    (DOCS / ".nojekyll").touch()
    print(f"built {len(issues)} issues, {len(audio_slugs)} with audio")

if __name__ == "__main__":
    main()
