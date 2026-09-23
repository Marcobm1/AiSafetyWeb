# AI Safety Web

I built this site to keep up with AI Safety research and news. It is a static
website that updates itself automatically once a day. On top of the daily
news, I curate two reading sections by hand: **Papers** (papers, essays,
reports, scenarios and posts, each with a short synopsis) and the **Library**
(books on themed shelves). Visitors can mark what they want to read or have
read on their own **My shelf**, which lives only in their browser.

**Live site (once deployed):** https://marcobm1.github.io/AiSafetyWeb/

- My full technical notes on how everything works: [docs/HOW_THIS_SITE_WORKS.md](docs/HOW_THIS_SITE_WORKS.md)
- My development log: [docs/DEVLOG.md](docs/DEVLOG.md)

## Quick start (Windows)

This is how I set up the project on a new computer:

```powershell
git clone https://github.com/Marcobm1/AiSafetyWeb.git C:\dev\AiSafetyWeb
cd C:\dev\AiSafetyWeb
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

I never clone this repository inside OneDrive (cloud sync can corrupt `.git/`).
