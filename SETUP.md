# Setup

Completed 2026-09-07. Kept for reference; CLAUDE.md is the living document.

- Repo: `~/Code/church-newsletter` → github.com/justinrolston/church-newsletter (public, `main`).
- Deps: `python3 -m venv .venv && source .venv/bin/activate && pip install markdown python-frontmatter edge-tts mutagen`.
- Build: `python scripts/build.py` (add `--force` to regenerate all audio, `--no-audio` for HTML only). Voice defaults to `en-US-AndrewNeural`; override with `TTS_VOICE=... python scripts/build.py --force`.
- GitHub Pages: `main` / `/docs`, custom domain `churchnews.therolstons.com`, HTTPS enforced.
- DNS (Google Cloud DNS): `CNAME churchnews → justinrolston.github.io`.
- Weekly job: Cowork scheduled task `church-newsletter-weekly`, Sundays 7:00am local, prompt = `JOB-PROMPT.md`. Runs only while the Claude desktop app is open. Unattended alternative: `0 7 * * 0 cd ~/Code/church-newsletter && claude -p "$(cat JOB-PROMPT.md)"`.
- Bot endpoints: `https://churchnews.therolstons.com/issues.json` (newest first; `html_url`, `md_url`, `mp3_url`) and podcast feed `https://churchnews.therolstons.com/feed.xml`.
- Retired: the old `watchmans-brief-weekly` task. The vault's `Justin's Note/Newsletter/` folder is an archive only.
