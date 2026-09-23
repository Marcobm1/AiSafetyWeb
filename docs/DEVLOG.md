# Development Log

My chronological record of every stage and change: what I did, why I did it,
which files changed, and what is still pending. Newest entries at the bottom.

---

## 2026-09-23 — Stage 1: Repository setup and initial documentation

**What I did**
- Today I installed Git 2.55, Python 3.12.10 and GitHub CLI 2.101 with `winget`.
- I moved the project out of OneDrive to `C:\dev\AiSafetyWeb`.
- I initialised Git with `main` as the default branch and added
  `https://github.com/Marcobm1/AiSafetyWeb.git` as the remote `origin`.
- I set my Git identity **locally** (`git config --local`), not globally.
- I created a Python 3.12 virtual environment (`.venv/`, ignored by Git) and
  pinned all dependencies in `requirements.txt`.
- I wrote `CLAUDE.md`, `README.md`, `docs/HOW_THIS_SITE_WORKS.md` and this log.
- I set a writing style for all my Markdown docs: first person, as my own
  technical notes, in English. I added it as a rule in `CLAUDE.md` and rewrote
  `README.md`, `docs/HOW_THIS_SITE_WORKS.md` and this log in that style.

**What I decided and why**
- **Python + Jinja2 as the site generator** (instead of Astro/Eleventy): I use
  one language for both fetching and building, and I don't have a Node.js
  toolchain to maintain. The generated HTML works without JavaScript.
- **Project outside OneDrive:** cloud sync can corrupt `.git/`. GitHub syncs
  my two computers instead.
- **Local Git identity with GitHub's noreply email:** the repo is public and
  commit emails are visible. A local setting doesn't affect my other repositories.
- **Pinned versions + `.python-version` = 3.12:** reproducible builds. My local
  machines and GitHub Actions use the same Python and package versions.
- **`.gitattributes` with LF line endings:** I edit on Windows and the site is
  built on Linux (Actions). LF in the repo avoids noisy whole-file diffs.
- **One JSON file per month for news, and a single workflow** (agreed plan).
  See HOW_THIS_SITE_WORKS §3 and §7.
- **First-person docs:** I also use these files to study and understand the
  project, so I want them to read like my own notes. `CLAUDE.md` is the
  exception: it stays as instructions for Claude.

**Files I created**
`CLAUDE.md`, `README.md`, `requirements.txt`, `.python-version`, `.gitignore`,
`.gitattributes`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Stage 2: fetch script and `config/sources.yaml` (verify every feed URL).
- Stage 3: site skeleton, `build_site.py`, local preview command.
- Stage 4: papers archive (verify every paper) and reading tracker.
- Stage 5: styles (serif, 680px column, light/dark).
- Stage 6: GitHub Actions workflow, Pages deployment, staleness warning.
- Stage 7: final documentation review.
