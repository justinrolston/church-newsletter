# Setup — one time, ~15 minutes

## 1. Create the repo

```bash
mv ~/path/to/church-newsletter ~/church-newsletter   # this folder
cd ~/church-newsletter
git init -b main
gh repo create church-newsletter --public --source=. --push
```

## 2. Build once locally (generates the 16 back-issue MP3s — a few minutes)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install markdown python-frontmatter edge-tts mutagen
python scripts/build.py
open docs/index.html          # sanity check
git add -A && git commit -m "Initial build, issues 01–16" && git push
```

Pick a voice: `edge-tts --list-voices | grep en-US`. Default is `en-US-AndrewNeural`; override with `TTS_VOICE=en-US-BrianNeural python scripts/build.py --force`.

## 3. GitHub Pages

Repo → Settings → Pages → Source: **Deploy from a branch** → `main` / `/docs` → Save.
Custom domain: `churchnews.therolstons.com` → Save → tick **Enforce HTTPS** once the cert issues (a few minutes after DNS resolves).

## 4. DNS (wherever therolstons.com lives)

```
CNAME   churchnews   →   <your-github-username>.github.io
```

Test: `dig churchnews.therolstons.com` then open https://churchnews.therolstons.com.

## 5. Schedule the job in Claude Code

`.gitignore` already excludes `.venv`. In Claude Code, from the repo:

```
/schedule
```
Weekly, Sunday 7:00am, prompt = contents of `JOB-PROMPT.md`.
(Or `crontab -e`: `0 7 * * 0 cd ~/church-newsletter && claude -p "$(cat JOB-PROMPT.md)" --allowedTools ...`)

## 6. Point the bot at it

- Latest issue index: `https://churchnews.therolstons.com/issues.json` (newest first; `html_url`, `md_url`, `mp3_url`)
- Podcast: `https://churchnews.therolstons.com/feed.xml` — add to Apple Podcasts / Overcast via "Add by URL".

## 7. Retire the old job

Delete the Cowork scheduled task `watchmans-brief-weekly`. The vault's `Justin's Note/Newsletter/` folder stays as-is as an archive; new issues live only in the repo.
