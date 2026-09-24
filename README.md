# AI Safety Web

I built this site to keep up with AI Safety research and news. It is a static
website that updates itself once a day: a GitHub Actions workflow collects new
posts from AI Safety blogs and new arXiv papers every morning at 06:00 UTC,
rebuilds the site and publishes it. On top of the daily news I curate, by hand:

- **Papers**: papers, essays, reports, scenarios and posts, each with a short synopsis;
- the **Library**: books on themed shelves, with their covers;
- **Start Here**: an ordered reading path for newcomers;
- **My Own Path**: my own public learning log (Timeline, Bookshelf and a monthly Journal).

Visitors can mark what they want to read or have read on their own **My shelf**,
which lives only in their browser.

**Live site:** https://marcobm1.github.io/AiSafetyWeb/

- My full technical notes on how everything works: [docs/HOW_THIS_SITE_WORKS.md](docs/HOW_THIS_SITE_WORKS.md)
- My development log (what I did, when and why): [docs/DEVLOG.md](docs/DEVLOG.md)

## Quick start (Windows)

This is how I set up the project on a new computer (details in
HOW_THIS_SITE_WORKS, sections 4 and 10):

```powershell
git clone https://github.com/Marcobm1/AiSafetyWeb.git C:\dev\AiSafetyWeb
cd C:\dev\AiSafetyWeb
git config --local user.name "Marco Barrera Martín"
git config --local user.email "87645460+Marcobm1@users.noreply.github.com"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then, every time I work on it:

```powershell
git pull                                   # the daily robot commits new data
python scripts\build_site.py --serve       # preview on http://localhost:8000/AiSafetyWeb/
# ... change something, then commit and push (a push redeploys the site)
```

I never clone this repository inside OneDrive (cloud sync can corrupt `.git/`).
