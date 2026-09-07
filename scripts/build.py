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
:root{color-scheme:light}*{box-sizing:border-box}
body{margin:0;background:#f4f1ea;color:#1c1a17;font-family:Georgia,"Iowan Old Style","Times New Roman",serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:680px;margin:0 auto;padding:0 20px 60px}
header.masthead{text-align:center;padding:44px 20px 28px;border-bottom:3px double #b9322f;margin-bottom:8px}
.kicker{font-family:"Helvetica Neue",Arial,sans-serif;text-transform:uppercase;letter-spacing:.28em;font-size:11px;color:#b9322f;font-weight:700;margin-bottom:14px}
h1.title{font-size:44px;line-height:1.05;margin:0 0 12px;font-weight:700;letter-spacing:-.5px}
h1.title a{color:inherit;text-decoration:none}
.tagline{font-style:italic;color:#5a5349;font-size:16px;margin:0 auto;max-width:480px}
.issueline{font-family:"Helvetica Neue",Arial,sans-serif;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#8a8378;margin-top:18px;font-weight:600}
.audio{margin:26px 0 0;padding:14px 16px;background:#fffdf8;border:1px solid #ddd6c8;border-radius:6px}
.audio label{display:block;font-family:"Helvetica Neue",Arial,sans-serif;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#8a8378;margin-bottom:8px}
.audio audio{width:100%}
.body blockquote{background:#fffdf8;border-left:4px solid #b9322f;padding:18px 22px;margin:30px 0 10px;font-size:17px;font-style:italic;color:#36322c;border-radius:2px}
.body blockquote p{margin:0}
.body hr{border:0;border-top:1px solid #ddd6c8;margin:30px 0 8px}
.body h2{font-family:"Helvetica Neue",Arial,sans-serif;font-size:15px;text-transform:uppercase;letter-spacing:.14em;font-weight:700;margin:22px 0 4px}
.body h2+p em{font-family:"Helvetica Neue",Arial,sans-serif;font-size:12px;color:#8a8378;font-style:normal}
.body p{margin:0 0 22px}
.body a{color:#b9322f;text-decoration:none;border-bottom:1px solid rgba(185,50,47,.3)}
.body a:hover{border-bottom-color:#b9322f}
.body .elder{background:#2c2a26;color:#ece7dc;border-radius:6px;padding:26px 28px;margin-top:34px}
.body .elder h2{color:#e8b04b;margin-top:0}
.body .elder h2+p em{color:#a39d8f}
.body .elder blockquote{background:transparent;border:0;padding:0;margin:0;color:#ece7dc;font-size:16.5px}
.body .elder strong,.body .elder em{color:#f3d99a}
footer.foot{text-align:center;font-family:"Helvetica Neue",Arial,sans-serif;font-size:12px;color:#8a8378;margin-top:36px;padding-top:22px;border-top:1px solid #ddd6c8;line-height:1.7}
ul.issues{list-style:none;padding:0;margin:30px 0}
ul.issues li{padding:16px 0;border-bottom:1px solid #ddd6c8}
ul.issues .d{font-family:"Helvetica Neue",Arial,sans-serif;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#8a8378}
ul.issues a{color:#1c1a17;text-decoration:none;font-weight:700;font-size:19px}
ul.issues .lede{font-style:italic;color:#5a5349;margin-top:6px}
ul.issues .links{font-family:"Helvetica Neue",Arial,sans-serif;font-size:12.5px;margin-top:6px}
ul.issues .links a{color:#b9322f;font-weight:400;font-size:12.5px}
@media(max-width:480px){h1.title{font-size:34px}}
"""

def page(title, body, extra_head=""):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="{SITE}/feed.xml">{extra_head}
<style>{CSS}</style></head><body><div class="wrap">
<header class="masthead"><div class="kicker">Weekly Digest · SBC · Reformed · Theology</div>
<h1 class="title"><a href="{SITE}/">{TITLE}</a></h1><p class="tagline">{TAGLINE}</p>{{ISSUELINE}}</header>
{body}
<footer class="foot">{TITLE} · <a href="{SITE}/feed.xml" style="color:#8a8378">Podcast feed</a><br>Reply with corrections or tips. Forward to a fellow elder.</footer>
</div></body></html>"""

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

def render_issue(i, has_audio):
    md = markdown.Markdown(extensions=["smarty"])
    body_html = md.convert(i["body"])
    # wrap the Elder's Desk section in the dark block
    body_html = re.sub(r'(<h2>🧭 For the Elder.*?)(?=<hr\s*/?>|<p><em>State of the Church Today ·)',
                       r'<div class="elder">\1</div>', body_html, flags=re.S)
    issueline = f'<div class="issueline">Issue {i["issue"]:02d} · {i["date"].strftime("%A, %B %-d, %Y")}</div>'
    audio = ""
    if has_audio:
        audio = f'<div class="audio"><label>Listen to this issue</label><audio controls preload="none" src="{SITE}/audio/{i["slug"]}.mp3"></audio></div>'
    out = page(i["title"], f'{audio}<div class="body">{body_html}</div>')
    return out.replace("{ISSUELINE}", issueline)

def render_index(issues, audio_slugs):
    items = []
    for i in reversed(issues):
        links = [f'<a href="issues/{i["slug"]}.html">Read</a>']
        if i["slug"] in audio_slugs: links.append(f'<a href="audio/{i["slug"]}.mp3">Listen</a>')
        links.append(f'<a href="{SITE}/issues/{i["slug"]}.md">Markdown</a>')
        items.append(f'<li><div class="d">Issue {i["issue"]:02d} · {i["date"].strftime("%B %-d, %Y")}</div>'
                     f'<a href="issues/{i["slug"]}.html">{html.escape(i["title"])}</a>'
                     f'<div class="lede">{html.escape(i["lede"])}</div><div class="links">{" · ".join(links)}</div></li>')
    out = page(TITLE, f'<ul class="issues">{"".join(items)}</ul>')
    return out.replace("{ISSUELINE}", '<div class="issueline">Every Sunday</div>')

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
    return intro + t + "\n\nThat's this week's State of the Church Today. Forward it to a fellow elder."

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
    (DOCS / "index.html").write_text(render_index(issues, audio_slugs))
    (DOCS / "feed.xml").write_text(build_feed(issues, audio_slugs))
    (DOCS / "issues.json").write_text(json.dumps([{
        "issue": i["issue"], "date": i["date"].isoformat(), "title": i["title"], "lede": i["lede"],
        "html_url": f"{SITE}/issues/{i['slug']}.html", "md_url": f"{SITE}/issues/{i['slug']}.md",
        "mp3_url": f"{SITE}/audio/{i['slug']}.mp3" if i["slug"] in audio_slugs else None,
    } for i in reversed(issues)], indent=2))
    (DOCS / ".nojekyll").touch()
    print(f"built {len(issues)} issues, {len(audio_slugs)} with audio")

if __name__ == "__main__":
    main()
