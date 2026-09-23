# AI Safety Web

I built this site to keep up with AI Safety research and news. It is a static
website that updates itself automatically once a day, plus a Library of
important AI Safety readings (papers, essays, reports…) that I curate by hand.

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
