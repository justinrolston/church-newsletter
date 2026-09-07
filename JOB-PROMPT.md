Produce this week's issue of "State of the Church Today" and publish it. Follow CLAUDE.md exactly.

1. Determine the issue number (highest NN in issues/ + 1) and use today's date.
2. Research all five beats with web search. Check wng.org, founders.org, and grimkeseminary.org directly. Use mbcpathway.com for SBC news. Verify every story is from the last 7–10 days and every URL came from a real result.
3. Write issues/YYYY-MM-DD-issue-NN.md modeled on the most recent issue.
4. Run: source .venv/bin/activate && python scripts/build.py
5. Confirm docs/audio/YYYY-MM-DD-issue-NN.mp3 exists and docs/audio/YYYY-MM-DD-issue-NN.txt reads cleanly (no URLs, no markdown).
6. git add -A && git commit -m "Issue NN — YYYY-MM-DD" && git push
7. Report: lead stories in 2–3 sentences, beats with no real news, sources that yielded nothing usable, and the live URL https://churchnews.therolstons.com/issues/YYYY-MM-DD-issue-NN.html
