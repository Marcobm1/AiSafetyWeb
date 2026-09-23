# CLAUDE.md — permanent rules for this project

These rules apply to every Claude session working on this repository.

## Language
- **Talk to the owner (Marco) in Spanish**: explanations, plans, questions, summaries.
- **Everything else in English**: website content and UI, code, code comments,
  commit messages, and everything in `docs/`.

## Where the project lives
- Marco works from two computers, each with its own working copy:
  - work computer: **`C:\dev\AiSafetyWeb`**
  - home computer: **`C:\Users\bymar\Desktop\Varios\Proyectos\AI Safety Web`**
  Work from whichever of the two the session was opened in.
- **Never put the repository inside OneDrive** (or Dropbox/Google Drive) on any
  computer. Cloud-sync tools rewrite files inside `.git/` while Git is using them,
  which can corrupt the repository. GitHub is the sync mechanism between computers.

## Working routine (two computers + a daily bot)
1. **Before starting**: `git pull` (the GitHub Action commits new data every day,
   so the remote almost always has new commits).
2. Make the change.
3. **Update the documentation in the same commit** (see below).
4. **When finished**: commit with a clear English message, then `git push`.
- **Transparency (Marco's decision):** keep the `Co-Authored-By: Claude …`
  trailer in every commit Claude makes, and keep the line "Built with the help
  of Claude Code." in About.
- If a push fails because Git is not authenticated with GitHub, **stop** and
  explain how to authenticate (`gh auth login`). Do not look for workarounds.
- Git identity is configured **locally** for this repository only
  (`git config --local`), never `--global`.

## Documentation is part of every change (mandatory)
A change is not finished until the docs reflect it, in the same commit:
- **`docs/HOW_THIS_SITE_WORKS.md`** — always describes the *current* state of the
  project (architecture, files, scripts, workflow, how-tos, troubleshooting, glossary).
  Written for a technical reader who is new to web development.
- **`docs/DEVLOG.md`** — append a dated entry: what was done, why each relevant
  decision was taken, files created/changed, what is still pending.

## Writing style for Markdown documents (mandatory)
Applies to every reader-facing `.md` file: `README.md`, `docs/HOW_THIS_SITE_WORKS.md`,
`docs/DEVLOG.md` and any `.md` created in the future.
- Write in **first person, as Marco** (e.g. "I built this site to...",
  "I chose Python + Jinja2 because...", "When I work from my second computer, I...").
- Tone of **personal technical notes**: clear, direct and didactic. Marco also
  uses these files to study and understand the project, so explain the *why*.
- Still in **English**.
- `docs/DEVLOG.md` entries are first person too ("Today I set up...", "I decided to...").
- **Exception:** `CLAUDE.md` stays written as instructions for Claude, not in first person.

## Ask, don't assume
If something is ambiguous, ask Marco before assuming.

## Hard rules for content
- Never republish full articles: title, source, date, a short excerpt (max ~2
  sentences) and a link to the original.
- Never invent feed URLs or paper details. Verify every feed URL and every
  paper (title, authors, year, URL) against the real source; drop what cannot be verified.
- Respect the arXiv API terms (rate limits, pauses between requests).
- Every **Papers** and **Library** entry (title, authors, year, type, URL and,
  for books, the Open Library OLID / cover id / ISBN and the edition) must be
  verified against the original source, not just against a curriculum or
  listing. If the publisher's or author's page can't be reached from Marco's
  network, use another reliable source (Wikipedia, WorldCat, an archived copy
  of the official page on the Wayback Machine) before dropping an entry.
  Strip tracking parameters (e.g. `utm_source`) from URLs. Drop what cannot be
  verified and tell Marco.
- **Publishing rule (papers and books):** an entry is published only if it has
  a `synopsis` without `TODO`. `why_it_matters` and `my_opinion` are optional
  and shown only when present. Claude may draft a `synopsis`: 2–4 neutral
  sentences in its own words, based on the verified source; never copy text
  from the publisher, Amazon, Goodreads, reviews or the abstract.
  **Never write or invent `my_opinion`**: only Marco writes it.
- Books: use the most recent English edition (verified; a new numbered or
  revised edition counts, a reprint in another format doesn't). Covers are always
  loaded from `covers.openlibrary.org` by **cover id or OLID** (never by ISBN:
  ISBN lookups are rate-limited to 100 requests / 5 min per IP); never
  download cover images into the repo. `free_url` only for free versions
  published officially by the authors or publisher, never unauthorised copies.
- **`data/my_path/` (timeline + reading log) is Marco's personal record.**
  Never invent its dates, months, statuses or notes: ask him. Placeholder notes must be clearly marked
  `TODO(Marco)` so they are obvious to replace.
- Paper candidate abstracts follow the excerpt rule (max ~2 sentences).
- Before stating how many duplicates the fetch script finds, or changing the
  title-based duplicate check, test it against the real data (it only
  compares titles between two different sources marked `crossposts: true`).

## Architecture summary
- **Static site** generated by a small Python script with Jinja2 templates
  (no Node, no framework). Output goes to `_site/` (not committed).
- **Daily update**: one GitHub Actions workflow,
  `.github/workflows/update-and-deploy.yml` (cron 06:00 UTC + manual + on
  push to main). Daily/manual runs: `fetch_news.py` → commit data only if it
  changed (as github-actions[bot], `git pull --rebase` before pushing) →
  `build_site.py` → deploy with `upload-pages-artifact` + `deploy-pages`.
  Push runs skip the fetch (`github.event_name == 'push'`). A manual run with
  the `check_feed` input only tests one feed (`fetch_news.py --check-feed`).
- **Workflow rules:** `permissions: {}` at the top and minimal per-job
  permissions (build: `contents: write`; deploy: `pages: write`,
  `id-token: write`); `concurrency` without cancelling; **every action pinned
  to a full commit SHA with the version in a comment** (the repository
  requires it, and only GitHub-made `actions/…` are allowed); workflow inputs
  go through `env:`, never interpolated into `run:`. Never add a permission or
  a third-party action without asking Marco.
- **Stale-data warning:** every page carries a hidden notice that
  `static/js/stale.js` shows when `last_run` (data/status.json) is older than
  `stale_after_hours` (config/site.yaml, 48) by the visitor's clock.
- **Site URL**: https://marcobm1.github.io/AiSafetyWeb/ — every internal link and
  asset must use the base path `/AiSafetyWeb/` (set once in `config/site.yaml`).
  Templates build internal links only with the `url('...')` helper, never by
  hand; `build_site.py` fails the build on any broken internal link.
- Pages must work **without JavaScript**; JS only adds extras (filters, tracker,
  theme toggle). Feed data is always autoescaped and external links go through
  the `safe_url` filter (http/https only).
- **Reading tracker** (To read / Read) lives only in the visitor's browser
  (localStorage, always wrapped in try/catch) behind a `ReadingStore` interface
  (`static/js/reading-store.js`) so a server-backed store can be added later.
  The **My shelf** page lists the visitor's marks and offers JSON export/import;
  it must say clearly that marks are stored only in that browser.
- **Two reading sections, two data files:**
  - **Papers** (papers, essays, reports, scenarios, blog posts) → `data/papers.yaml`.
  - **Library** (books only, on themed shelves, with Open Library covers) →
    `data/books.yaml`. Each book has its own page (`library/<id>/`, the no-JS
    fallback) and opens in a native `<dialog>` card on the shelf.
  Every entry has a stable `id`, **unique across both files** (the build checks
  it). Papers, Library, **Start Here**, **My Own Path** (`paper_ref` /
  `book_ref` in the reading log) and the reading tracker all refer to entries
  by that `id`; never duplicate entry data.
- **Start Here** has no separate file: stages are listed under
  `start_here_stages` in `data/papers.yaml`, and an entry joins the path via
  its own `start_here: {stage, order, note}` block.
- **Menu:** the site title links to the home page (Today); the menu is
  News · Papers · Library · Start Here · My Own Path · About (only pages that
  exist); "My shelf" is a small separate link in the header.
- **Design (Stage 6, approved by Marco): an e-reader page.** Literata as the
  only typeface, **self-hosted** in `static/fonts/` with its OFL licence (never
  Google Fonts or another font CDN); sepia paper / near-black, ink-only
  colours (links are text colour + underline); 620px column; chapter-style
  titles. Colours are tokens on `:root`, redefined for dark mode (media query
  + `[data-theme="dark"]`). Every text colour must meet WCAG AA (4.5:1; 3:1
  for large text): recheck the table in HOW_THIS_SITE_WORKS §6.8 on any colour
  change. Keyboard focus must stay clearly visible. Drop cap (`drop-cap`) only
  on pages with an introduction, never on list pages.
- **My Own Path v2:** page order Timeline → Bookshelf → Journal. The Journal
  is computed by `build_journal()` from `timeline.yaml` + `reading_log.yaml`
  (no file of its own): one month at a time, grouped by type; without JS all
  months are shown. Reading types: paper, report, essay, article, book,
  resource, podcast-video; Timeline types: course, project, milestone. The
  validation rules live in `check_timeline_item` / `check_log_entry`, shared
  by the build and the form: change them there, never duplicate them.
- **Local "Add entry" form (`scripts/local_form.py`, `templates/local/`):**
  only the preview server (`build_site.py --serve`) generates it, in memory.
  It must never be written to `_site/` or put in `static/` (the build fails on
  its markers `data-local-only` / `/_local/`). It inserts text into the YAML
  (never re-dumps it), validates the whole file before replacing it, rebuilds
  the preview and **never commits or pushes**. Keep its protections: server on
  127.0.0.1 only, Host check (DNS rebinding), Origin/Referer check, per-run
  random token, 64 KB limit. When testing it, use a temporary copy of the
  repository, never Marco's real data files.
- Paper candidates are **not shown on the website**; they only live in the repo.
- **Paper candidates**: the daily script writes new arXiv papers to
  `data/paper_candidates.json` (machine-written, auto-pruned). Marco promotes
  one to `data/papers.yaml` with `scripts/promote_candidate.py` (it appends a
  block with `synopsis`/`difficulty` as TODO, so it is not published yet).
- Python **3.12** everywhere (local venv in `.venv/` and in Actions); pinned
  versions in `requirements.txt`.

## Plan (stages)
- ✅ 1–6: setup, news fetching, site skeleton, Papers + Library, Start Here +
  My Own Path, design.
- ✅ **7: My Own Path v2** (approved): Timeline, Bookshelf, a monthly Journal
  (replaces the Reading log) and a local-only "Add entry" form.
- ✅ **8: GitHub Actions + GitHub Pages**: the site is published.
- **9: final documentation review.**
- Before merging any experimental change, try it on a branch (see
  HOW_THIS_SITE_WORKS §10, "Trying a change on a branch").

## Folder structure
```
config/sources.yaml      all news sources, arXiv query, karma thresholds, topic keywords
config/site.yaml         site title, base path, settings
data/papers.yaml         Papers: curated papers, essays, reports... (by hand); also
                         holds the Start Here stage list and each entry's start_here block
data/books.yaml          Library: books on themed shelves (by hand)
data/my_path/timeline.yaml     My Own Path: courses, projects, milestones (by hand)
data/my_path/reading_log.yaml  My Own Path: everything Marco reads/watches, by month
                         (by hand or with the local form; shown in the Journal)
data/paper_candidates.json  arXiv candidates for the archive (written by the bot, auto-pruned)
data/news/YYYY-MM.json   aggregated news entries, one file per month
data/status.json         last run time + per-source status
scripts/fetch_news.py    fetch feeds + arXiv, dedupe by URL, save JSON + candidates
scripts/promote_candidate.py  copy a candidate into papers.yaml as a new block
scripts/build_site.py    render templates + data into _site/; --serve = local preview
                         (fetch_news.py --check-feed URL tests one feed, writes nothing)
scripts/local_form.py    the local-only "Add entry" form (preview server only)
templates/               Jinja2 HTML templates (templates/local/: the local form, never built)
static/css, static/js    styles and small vanilla JS modules (filters, reading-store,
                         tracker, my-shelf, library, theme, journal)
static/fonts/            Literata (self-hosted .woff2) + its OFL licence
docs/                    HOW_THIS_SITE_WORKS.md, DEVLOG.md
.github/workflows/       update-and-deploy.yml (the only workflow)
```
