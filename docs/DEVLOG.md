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

---

## 2026-09-23 — Plan update: paper candidates, Start Here and My Own Path

**What I did**
- Before starting Stage 2, I added three features to the plan and fixed the
  data formats for all of them (see HOW_THIS_SITE_WORKS §3.1):
  1. **Paper candidates:** the daily script also saves new arXiv papers to
     `data/paper_candidates.json`, skipping duplicates and papers I've already
     curated, and pruning old ones. I promote one with `scripts/promote_candidate.py`.
  2. **Start Here:** an ordered reading path for newcomers, built from entries
     in `data/papers.yaml` that have a `start_here` block (stage, order, note).
     `papers.yaml` gets a `type` field (paper, essay, report, scenario, blog-post).
  3. **My Own Path:** my public learning log in `data/my_path.yaml`, shown as a
     timeline with filters and counters.
- I checked which AI Safety curricula exist today, to base Start Here on them:
  BlueDot Impact currently runs **AGI Strategy**, **Technical AI Safety**,
  **Frontier AI Governance** and **Biosecurity**, plus the short self-paced
  **Future of AI**. I verified that `https://bluedot.org/courses/future-of-ai`
  and `https://bluedot.org/courses/agi-strategy` exist and that the course names
  are "Future of AI" and "AGI Strategy".
- I added rules to `CLAUDE.md`: verify every Start Here entry against the
  original source, never invent anything in `my_path.yaml`, and keep candidate
  abstracts to ~2 sentences.

**What I decided and why**
- **One file for all readings, linked by `id`:** Start Here and My Own Path
  point to entries in `papers.yaml` instead of copying them. Each reading's
  data lives in one place, and the reading tracker works everywhere with the
  same key.
- **Candidates in JSON, archive in YAML:** the candidates file is rewritten by
  the bot every day (JSON is safer for that); the archive is edited by me
  (YAML is friendlier and allows comments).
- **Candidate `id` = arXiv number without version:** a v2 of the same paper
  never shows up as a new candidate.
- **Pruning after a configurable number of days** (default 60): the file stays
  small, and a paper I haven't promoted in two months probably doesn't need it.
- **Promotion script appends text instead of rewriting YAML:** loading and
  re-saving YAML with PyYAML would delete my comments. Unfinished entries
  (still containing `TODO`) are skipped by the build, so they never go live.
- **Start Here and My Own Path in a new Stage 5:** Stage 4 builds the archive
  and the reading tracker; Start Here reuses both, so it goes right after. Its
  entries need careful verification, so it deserves its own stage.

**Files changed**
`CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Revised plan (8 stages)**
- ✅ Stage 1: repository setup and initial documentation.
- Stage 2: `config/sources.yaml` (verify every feed URL), `scripts/fetch_news.py`,
  news JSON, `status.json`, **paper candidates with pruning**, and an empty
  `data/papers.yaml` with the documented format.
- Stage 3: site skeleton, `build_site.py`, local preview command.
- Stage 4: papers archive (with `type`), reading tracker, `promote_candidate.py`.
- Stage 5 (new): **Start Here** (stages + verified readings, tracker included)
  and **My Own Path** (timeline, filters, counters, step-by-step how-to).
- Stage 6: styles (serif, 680px column, light/dark).
- Stage 7: GitHub Actions workflow, Pages deployment, staleness warning.
- Stage 8: final documentation review.

**Pending decisions**
- Whether paper candidates are shown on the website or only kept in the repo.
- The name of the archive section ("Papers" vs "Library").
- Status and dates of my two BlueDot courses (first entries of My Own Path).

---

## 2026-09-23 — Plan decisions: Library, Start Here inside library.yaml, candidates repo-only

**What I did**
- I settled the pending decisions from the plan update and made the docs
  consistent with them.

**What I decided and why**
- **Paper candidates stay in the repo only**, not on the website. New arXiv
  papers already appear on the home page and in the news archive, so a public
  "Recent papers" page would duplicate them and mix unreviewed papers with my
  curated selection. I documented how to add a hidden (unlinked, `noindex`)
  review page later if reading the JSON becomes tedious (HOW_THIS_SITE_WORKS §9).
- **"Papers" is now "Library"** everywhere: the section name, the data file
  (`data/papers.yaml` → `data/library.yaml`) and the docs. The archive holds
  essays, reports, scenarios and blog posts too, so "Papers" was misleading.
  (Older DEVLOG entries keep the old name because they record what I thought then.)
- **No separate `start_here.yaml`.** The stage list lives under
  `start_here_stages` at the top of `library.yaml`, and each reading joins the
  path with its own `start_here: {stage, order, note}` block. One file, no
  duplicated data, and the path can't point to something missing from the
  Library. `entries` must stay the last key so `promote_candidate.py` can append.
- **My Own Path uses `date` + optional `completed`**, so I can record both when
  I started and when I finished.
- **My first two My Own Path entries** (created in Stage 2 as data): Future of
  AI, 2026-09-07 → 2026-09-11, completed; AGI Strategy, started 2026-09-12,
  in progress. Their notes are placeholders marked `TODO(Marco)`.

**Files changed**
`CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Stage 2 starts now (see the revised plan in the previous entry).
