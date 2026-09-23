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

---

## 2026-09-23 — Stage 2: News fetching, paper candidates and data formats

**What I did**
- I wrote `config/sources.yaml` with 13 RSS/Atom sources plus the arXiv query,
  karma thresholds, candidate retention and topic keywords. I checked every
  feed URL (HTTP 200 + valid feed) before adding it.
- I wrote `scripts/fetch_news.py` (see HOW_THIS_SITE_WORKS §5). It downloads
  the feeds and arXiv, normalises and deduplicates entries, saves them to
  `data/news/YYYY-MM.json`, updates `data/paper_candidates.json` and writes
  `data/status.json`. It has a `--dry-run` mode.
- I created `data/library.yaml` (empty, with the format documented in comments)
  and `data/my_path.yaml` with my first two entries: Future of AI
  (2026-09-07 → 2026-09-11, completed) and AGI Strategy (started 2026-09-12,
  in progress). Their notes are `TODO(Marco)` placeholders.
- First real run: 14/14 sources OK, 137 entries (all September 2026), 100 paper
  candidates. A second run added nothing, which confirms the deduplication works.

**What I decided and why**
- **Karma filtering on LessWrong's side** (`karmaThreshold` URL parameter):
  their feeds don't include karma, but the site filters for me. I checked that
  different thresholds really return different posts.
- **`max_age_days: 14`:** OpenAI's feed returns 1,219 items (its whole
  history). Without an age limit the first run would import years of posts.
- **`require_topic` for general sources** (LessWrong, OpenAI, DeepMind, Zvi,
  Transformer, Epoch, BlueDot, GovAI): they also post off-topic things. GovAI's
  feed turned out to be mostly job postings.
- **Topics from the title + first 600 characters:** LessWrong/AF feeds contain
  the whole post, and on the first try almost every post got all five topics.
- **Whole-word keyword matching with an explicit `*` for prefixes:** simple
  prefix matching made `AGI` match "agile".
- **arXiv query without plain "interpretability":** I measured one week of
  papers per phrase; "interpretability" alone matched ~195 papers a week, most
  of them generic explainability. The remaining phrases give ~10–15 a day.
- **One arXiv request per run** (100 newest results, sorted by submission
  date): far below arXiv's rate limits; the retry waits ≥ 3 s as they ask.
- **Cross-posts:** LessWrong and the AF share post ids, so duplicates are
  detected by post id; AF is listed first so it keeps the cross-post.
- **Only papers new to the news files become candidates:** an expired
  candidate can't come back just because arXiv still lists it.
- **Exit code 1 only if every source fails:** one broken feed is normal; all
  of them failing means a problem on my side that should trigger GitHub's email.
- **No Anthropic, Apollo Research, UK AISI or CAIS-blog feeds:** I couldn't find
  a working RSS feed for them, so I didn't invent one. Google DeepMind's own feed
  failed from my work network, so I use the one on `blog.google`.

**Files created / changed**
Created: `config/sources.yaml`, `scripts/fetch_news.py`, `data/library.yaml`,
`data/my_path.yaml`, `data/news/2026-09.json`, `data/paper_candidates.json`,
`data/status.json`. Changed: `.gitignore` (`*.tmp`),
`docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Replace the `TODO(Marco)` notes in `data/my_path.yaml` with my own takeaways.
- Review the source list and keywords after a few days of real data.
- Stage 3: site skeleton, `config/site.yaml`, `build_site.py`, local preview.

---

## 2026-09-23 — Source adjustments and My Own Path redesign

**What I did**
- **Interpretability on arXiv:** instead of dropping it, I added precise
  combinations (`arxiv.combinations` in `config/sources.yaml`):
  interpretability AND ("AI safety" | "AI alignment" | deception | deceptive),
  on top of the "mechanistic interpretability" and "sparse autoencoder"
  phrases. Measured on one week (2026-09-15..22): plain interpretability = 195
  papers, AND safety = 12 (mostly noise), AND alignment = 33 (noise),
  "mechanistic interpretability" = 6, AND "AI safety"/"AI alignment" = 1,
  AND deception = 4. The full query went from 71 to 74 papers a week.
- **CAIS AI Safety Newsletter:** already a source. `newsletter.safe.ai` is its
  Substack on a custom domain (the feed is generated by Substack, and
  `aisafety.substack.com` redirects there).
- **Anthropic:** the Alignment Science blog (`alignment.anthropic.com`) has no
  feed (no `<link rel="alternate">`, the usual feed paths return 404), so I
  left it out. The interpretability research site, **Transformer Circuits
  Thread**, has a valid Atom feed, so I added it as a source with a new
  `default_topics: [interpretability]` option.
- **Retries:** the arXiv API answered 429 (too many requests) after my many
  test queries today. The retry now honours the `Retry-After` header and waits
  at least 30 s on 429/503.
- **My Own Path redesign** (data format and docs now; page in Stage 5):
  - `data/my_path.yaml` became `data/my_path/timeline.yaml` (courses, projects,
    milestones; `id`, `date`, optional `completed`) with ids `future-of-ai` and
    `agi-strategy`.
  - New `data/my_path/reading_log.yaml` (everything I read, by `month`, with
    optional `archive_url`, `via` and `library_ref`). Empty for now: I'll add my
    September readings once they're verified and the page exists.
  - Step-by-step guides for adding a reading and a timeline stage (HOW §9).

**What I decided and why**
- **Two files instead of one `my_path.yaml` with two sections:** the reading
  log will grow much faster than the timeline; their shapes differ (days vs
  months, different types); an indentation slip in one file can't move an
  entry into the other section; and Git history shows readings and timeline
  changes separately. The `data/my_path/` folder keeps them together.
- **Reading-log types are their own list** (paper, report, essay, article,
  book, resource) and `type` is always required, even with `library_ref`,
  because the Library uses a different list (it has *scenario* and *blog-post*).
- **`month` written in quotes** (`"2026-09"`): unquoted, YAML could read some
  values as numbers or dates.
- **`via` links to a timeline `id`:** on the site, a reading with `via` will
  show the course and link to its stage in the timeline (`#timeline-<id>`).
- **Kept Zvi** as a source, with the same `require_topic` filter as before; if he
  floods the home page, I'll filter him harder (e.g. stricter keywords, like GovAI).

**Files created / changed**
Created: `data/my_path/reading_log.yaml`. Moved: `data/my_path.yaml` →
`data/my_path/timeline.yaml`. Changed: `config/sources.yaml`,
`scripts/fetch_news.py`, `CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`,
`docs/DEVLOG.md`.

**Updated plan**
- Stage 3: site skeleton, `config/site.yaml`, `build_site.py`, local preview.
- Stage 4: Library, reading tracker, `promote_candidate.py`.
- Stage 5: Start Here + My Own Path (timeline with duration bars and expandable
  notes; reading log grouped by month with counters, type filters, a readings
  per month chart, `archive_url` links and `via` links to the timeline).
  The build validates `via`, `library_ref`, `month` and URLs.
- Stage 6: styles.
- Stage 7: GitHub Actions + Pages. **Also: test Google DeepMind's own feed
  (`deepmind.google/blog/rss.xml`) from Actions and switch to it if it works**
  (it only fails from my work network).
- Stage 8: final documentation review.

---

## 2026-09-23 — Stage 3: Site skeleton, generator and local preview

**What I did**
- I wrote `config/site.yaml` (title, `site_url`, `base_path`, the 48-hour
  home-page window, topic labels, the menu).
- I wrote `scripts/build_site.py`. It rebuilds `_site/` from scratch, copies
  `static/`, renders the home page, the news archive (index + one page per
  month), About and a 404 page, and then checks every internal link. With
  `--serve` it previews the site on `http://localhost:8000/AiSafetyWeb/`.
- I wrote the templates (`base.html`, `_macros.html`, `index.html`,
  `news_index.html`, `news_month.html`, `about.html`, `404.html`), a basic
  stylesheet and `static/js/filters.js` (source/topic filters on month pages).
- I added a **second duplicate check by title** to `fetch_news.py` after
  finding three Redwood Research posts that were also on the Alignment Forum
  under different URLs, and removed those three duplicates from
  `data/news/2026-09.json` (134 entries now).
- I tested the preview: `/` redirects to `/AiSafetyWeb/`, every page returns
  200, unknown pages return our 404 page, and `/static/…` without the base
  path fails just like it would on GitHub Pages.

**What I decided and why**
- **`url()` helper + automatic link check:** the base path is the classic
  GitHub Pages trap. Templates never write internal links by hand, and the
  build fails if any `href`/`src` misses the base path or points to a missing
  file. I tested it by planting a bad link: the build failed with a clear message.
- **The preview serves under `/AiSafetyWeb/`**, not at the root, so it behaves
  like the real site.
- **The home window counts back from the last fetch, not from build time:** a
  rebuild days later still shows the latest batch instead of an empty page.
- **arXiv in its own collapsible block on the home page:** 15–20 papers a day
  would otherwise bury the posts from the other sources.
- **Security in the generator:** autoescaping, `StrictUndefined`, http(s)-only
  links from feeds (`safe_url`), `rel="noopener"` on external links.
- **Progressive enhancement:** everything works without JavaScript; the filter
  menus are hidden until the script shows them.
- **Title duplicates need ≥ 4 words:** short titles are too generic to compare.
- **Menu only lists pages that exist:** Library, Start Here and My Own Path
  join it in Stages 4–5.

**Files created / changed**
Created: `config/site.yaml`, `scripts/build_site.py`, `templates/*.html`,
`static/css/style.css`, `static/js/filters.js`. Changed:
`scripts/fetch_news.py` (title dedupe), `data/news/2026-09.json` (3 duplicates
removed), `CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Stage 4: Library page, reading tracker (`ReadingStore`, localStorage),
  `promote_candidate.py`.
- Replace the `TODO(Marco)` notes in `data/my_path/timeline.yaml`.
- Add my September readings to `data/my_path/reading_log.yaml` once the
  My Own Path page exists (Stage 5).

---

## 2026-09-23 — Narrower title-based duplicate check

**What I did**
- I reviewed the title-based duplicate check I added in Stage 3. It compared
  normalised titles (4+ words) between **any** two entries, even from the same
  source, so generic titles in unrelated blogs could be merged by mistake.
- I tested it against real data: the Stage 2 news file, the current one, and
  every item currently in all 14 feeds (1,611 items, no karma/age/topic filter).
- I replaced it with a narrower rule (`SeenIndex` in `scripts/fetch_news.py`):
  the title only counts between two **different** sources marked
  `crossposts: true` in `config/sources.yaml`. I marked the Alignment Forum,
  LessWrong, Redwood Research and METR, because I saw real cross-posts from them.

**What I decided and why**
- **Not "same title + same author":** the author never matched in the real
  cross-posts. The AF shows usernames (`Jozdien`, `ryan_greenblatt`) and
  Redwood's blog shows real names or another co-author (`Arun Jose`,
  `Nathan Sheffield`), so that rule would miss all of them.
- **Not within one source:** OpenAI has two different pages titled "The state
  of enterprise AI"; the old rule would have merged them. Within one source the
  URL check is enough.
- **Only sources with a proven cross-post get the flag**, so I don't widen the
  rule on a guess.

**Results** (the numbers of duplicates found by title)
- Stage 2 file (137 entries): 3, the three Redwood/AF posts I removed by hand.
- Current file (134 entries): 0.
- All current feed items (1,611): 4, the same three plus a joint METR/Redwood
  investigation published on both blogs. No false positives.
- Synthetic checks: the same generic title in Zvi and Transformer → not merged;
  twice in Redwood → not merged; in Redwood and the AF → merged.
- A real `--dry-run` of the fetch script runs cleanly (0/15 sources failed).

**Files changed**
`scripts/fetch_news.py`, `config/sources.yaml`, `docs/HOW_THIS_SITE_WORKS.md`,
`docs/DEVLOG.md`.

**Pending**
- Stage 4 is being redesigned (books and papers in separate sections) before I
  write any code; the plan comes in its own entry once I approve it.

---

## 2026-09-23 — Plan redesign: Papers and Library (books) as separate sections

**What I decided and why**
- **Books and papers are now two sections.** *Papers* (papers, essays,
  reports, scenarios, posts) is a filterable list with a synopsis per entry;
  the *Library* is books only, shown as shelves of real covers. They're browsed
  differently and need different fields, so they get separate files:
  `data/papers.yaml` (the old `library.yaml`, renamed) and `data/books.yaml`.
  I kept the name "Papers" for the list because it's short enough for the menu
  on a phone; the page's intro says it also holds essays, reports and posts.
- **Ids stay unique across both files**, so the reading tracker keeps one key
  per reading everywhere on the site.
- **Start Here stays in `papers.yaml`** (`start_here_stages` + each entry's
  `start_here` block).
- **New publishing rule:** an entry is published if it has a `synopsis`
  (2–4 neutral sentences in my own words, based on the verified source, never
  copied from publishers, Amazon, Goodreads, reviews or the abstract).
  `why_it_matters` and `my_opinion` are optional. Claude may draft synopses but
  never my opinion. Before, an entry needed my `why_it_matters` to go live,
  which would have kept the Papers page empty for a long time.
- **Menu:** the site title links to Today, the menu is News · Papers · Library ·
  Start Here · My Own Path · About, and "My shelf" is a small link in the header.
- **Library design (Stage 4b):** six shelves (AI Safety & Alignment; AI,
  Society & Governance; ML & Deep Learning; Mathematics for ML; Programming &
  Python; Thinking & Rationality), 2–4 books each, most recent English edition.
  Covers load from Open Library's Covers API by cover id / OLID (ISBN lookups are
  rate-limited to 100 per 5 minutes per IP), never downloaded; typographic
  cover when there is none. A book opens in a native `<dialog>` (Esc closes it);
  without JavaScript each book has its own page. Optional `free_url` only for
  official free versions.
- **My shelf:** each visitor's *To read* / *Read* marks on one page, with
  export/import, stored only in their browser. Public paths with accounts are
  documented as a possible future extension.
- **My Own Path → Bookshelf (Stage 5):** books from `reading_log.yaml`
  (`type: book`, with `status: reading | finished`, optional `started`, and
  `month` = month finished). `library_ref` becomes `paper_ref` / `book_ref`.
  My opinion lives only in `my_opinion` in papers/books.yaml; reading-log
  `notes` are for readings that are in neither.
- **A counterpoint on each side:** Katja Grace's "Counterarguments to the basic
  AI x-risk case" in Papers, and a book with a sceptical view on the AI Safety
  shelf (proposed: *AI Snake Oil*, Narayanan & Kapoor, 2024).

**Revised plan**
- ✅ Stages 1–3.
- ✅ **Stage 4a:** Papers, reading tracker (`ReadingStore`), My shelf with
  export/import, `promote_candidate.py`, publishing rule.
- **Stage 4b:** Library of books (shelves, covers, `<dialog>` cards, book pages),
  books in My shelf.
- **Stage 5:** Start Here + My Own Path (timeline, reading log, Bookshelf).
- Stage 6: styles. Stage 7: GitHub Actions + Pages. Stage 8: docs review.

---

## 2026-09-23 — Stage 4a: Papers, reading tracker, My shelf and promote_candidate.py

**What I did**
- I renamed `data/library.yaml` to `data/papers.yaml` and added **12 entries**,
  each verified against its original source (title, authors, year, type, URL):
  nine from the arXiv API in one request (Concrete Problems, Risks from Learned
  Optimization, Ngo et al., Carlsmith, Toy Models of Superposition, Shevlane et
  al., AI Control, Sleeper Agents, Alignment Faking), plus Cotra's Cold Takes
  essay, Katja Grace's counterarguments (AI Impacts) and AI 2027 (checked on
  their own pages). Toy Models links to its original on transformer-circuits.pub
  (arXiv id kept too). Synopses are Claude's drafts, written from the sources;
  `why_it_matters` and `my_opinion` are empty for me to fill in.
- **Dropped:** "Specification gaming: the flip side of AI ingenuity" (Krakovna
  et al., DeepMind, 2020). DeepMind's site fails with a TLS error from my work
  network, and I couldn't open an official copy elsewhere, so I couldn't verify
  it. To retry from home or once Actions runs (Stage 7).
- `build_site.py` now validates `papers.yaml` (required fields, slug ids, types,
  difficulties, topics, http(s) URLs without `utm_`, Start Here stages, ids
  unique across papers.yaml and books.yaml) and applies the publishing rule.
  It renders `papers/` and `my-shelf/`.
- New JavaScript: `reading-store.js` (the `ReadingStore` over localStorage),
  `tracker.js` (the buttons), `my-shelf.js` (lists, export, import).
  `filters.js` became generic, so the same script filters news and papers.
- `scripts/promote_candidate.py` appends a candidate to `papers.yaml` with
  `synopsis` and `difficulty` as TODO.
- `fetch_news.py` now reads `papers.yaml` to skip curated papers as candidates.
- The header: the title links to Today, a small "My shelf" link, and the menu is
  News · Papers · About (Library, Start Here and My Own Path join later).
- `reading_log.yaml`: format comments updated (`paper_ref` / `book_ref`, book
  `status` / `started`, `cover_id`, where `notes` apply). I did this now, not in
  4b as planned, because `library.yaml` no longer exists and the old comments
  pointed to it. The file still has no entries.

**How I tested it**
- Build: 7 pages, 12 papers, links OK. Broken data (unknown topic, `utm_` URL,
  duplicate id, bad type, missing URL, unknown stage) stops the build with a
  clear message; a missing synopsis or a TODO only skips that entry.
- `promote_candidate.py`: dry run, a real promotion (then reverted), and the
  errors (already promoted, unknown candidate, id taken, bad id).
- JavaScript in headless Edge against the local preview, with a throwaway test
  page: buttons and `aria-pressed`, filters (1 of 12 for type = scenario), saved
  format, My shelf lists and counts, moving between lists, removing a mark,
  export content, import (2 new, 1 changed, 2 invalid skipped, orphan note),
  a non-JSON file rejected, and corrupt storage not breaking the page. All passed.
- At 360 px wide, no page scrolls horizontally.

**Files created / changed**
Created: `data/papers.yaml` (renamed from `data/library.yaml`),
`scripts/promote_candidate.py`, `templates/papers.html`,
`templates/my_shelf.html`, `static/js/reading-store.js`, `static/js/tracker.js`,
`static/js/my-shelf.js`. Changed: `scripts/build_site.py`,
`scripts/fetch_news.py`, `templates/base.html`, `templates/_macros.html`,
`static/js/filters.js`, `static/css/style.css`, `config/site.yaml`,
`data/my_path/reading_log.yaml`, `CLAUDE.md`, `README.md`,
`docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Me: review the 12 synopses and difficulties; add `why_it_matters` /
  `my_opinion` where I want.
- Verify the DeepMind specification gaming post from another network.
- Stage 4b: books (list approved; sceptical pick to confirm: *AI Snake Oil*).

---

## 2026-09-23 — Stage 4b: the Library of books

**What I did**
- I created `data/books.yaml` with six shelves and **19 books**, each checked
  against the publisher's or author's page (title, subtitle, authors, edition,
  publisher, year) and against Open Library for the edition record (OLID),
  cover id and ISBN. I checked every cover image by eye on a contact sheet:
  all 15 covers match the right book and edition (the 3rd, 4th and 2nd edition
  covers show their edition). Four books have no cover on Open Library and get
  a typographic one: *AI Snake Oil*, *Understanding Deep Learning*,
  *Introduction to Probability* (2nd ed.) and *Automate the Boring Stuff* (3rd ed.).
- The synopses are Claude's drafts, written from the verified sources, not
  from publisher blurbs. `why_it_matters` and `my_opinion` are empty for me.
- `build_site.py` validates `books.yaml` with the same publishing rule as
  papers (plus shelf, OLID and cover id checks) and renders `library/`, one
  page per book (`library/<id>/`) and the books part of My shelf.
- New `static/js/library.js`: cover fallback, *To read / Read* badges on the
  shelf, and the book card in a native `<dialog>`.
- Library joined the menu; Papers links to it; About credits Open Library and
  explains that marks stay in the visitor's browser.

**What I decided and why**
- **Dropped *Life 3.0*** (Tegmark, 2017). I only found it on Open Library: the
  Penguin Random House page returned 404 and the author's MIT page didn't
  respond, so I couldn't check it against an official source. The AI, Society
  & Governance shelf has two books for now.
- **Hands-On ML: the 3rd edition (2022)** of *…with Scikit-Learn, Keras, and
  TensorFlow*. Géron's 2025 *…with Scikit-Learn and PyTorch* is a new book (its
  own 1st edition, per his repository), not a new edition of the one I approved.
- **"Most recent edition" = the latest numbered or revised edition**, not the
  latest paperback reprint. `year` is that edition's year.
- **`free_url` on 7 books**, only where the author or publisher offers the book
  free themselves: *Deep Learning*, *Understanding Deep Learning*, Sutton &
  Barto, *Mathematics for ML*, *Linear Algebra Done Right* (open access, CC
  BY-NC), *Automate the Boring Stuff* (CC licence) and *Rationality: From AI to
  Zombies* (linked as "Read Online" by MIRI). **Not** for Blitzstein & Hwang:
  its free PDF is on a Google Drive I couldn't confirm as official (Harvard's
  course page blocked my requests).
- **Covers by cover id only**, as the image `src` from covers.openlibrary.org
  (no downloads, no ISBN lookups). The typographic cover is always drawn
  underneath, so a missing or failed image never leaves a hole.
- **One `<dialog>` + `<template>` cards + a real page per book:** without
  JavaScript the link just goes to the book page; with it, the same card
  opens over the shelf. Native `<dialog>` gives focus handling, `Esc` and an
  inert background for free.
- **The same dialog on My shelf**, where books appear as a shelf of covers and
  papers as a list.

**How I tested it**
- Headless Edge against the local preview (24 checks): 19 books on 6 shelves,
  15 covers loaded, typographic cover where expected, dialog opens without
  leaving the page, is labelled by the title, takes focus, shows the buttons;
  marking *Read* adds the badge; the × and a backdrop click close it and focus
  returns to the book; the free link appears only where set; a broken image
  falls back to the typographic cover; My shelf shows books and papers in
  their groups and moves a book when its status changes in the dialog; the
  book page shows the saved mark. The Stage 4a tests (papers, export, import)
  still pass. No page scrolls horizontally at 360 px.
- The tests found one real bug: reopening a book right after closing the
  dialog left it empty, because the `close` event arrives late. Fixed.

**Files created / changed**
Created: `data/books.yaml`, `templates/library.html`, `templates/book.html`,
`templates/_book_dialog.html`, `static/js/library.js`. Changed:
`scripts/build_site.py`, `templates/_macros.html`, `templates/my_shelf.html`,
`templates/papers.html`, `templates/about.html`, `static/js/tracker.js`,
`static/js/my-shelf.js`, `static/css/style.css`, `config/site.yaml`,
`CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Me: review the 12 paper synopses (table in chat) and the 19 book synopses.
- Maybe find a verifiable third book for AI, Society & Governance, or retry
  *Life 3.0* from another network.
- Stage 5: Start Here + My Own Path (timeline, reading log, Bookshelf).

---

## 2026-09-23 — Library adjustments and Stage 5: Start Here and My Own Path

**Library adjustments**
- **Introduction to Probability** now has `free_url: http://probabilitybook.net`.
  Harvard's Stat 110 page blocks requests from my network (403), so I read
  its Wayback Machine copy (2 Sep 2026), which says: "A free online version of
  the second edition … is now available at http://probabilitybook.net".
- **Life 3.0** (Tegmark) is back on AI, Society & Governance. I verified it on
  Wikipedia (title, subtitle, Knopf, 2017, first edition, ISBN 9781101946596,
  OCLC 973137375), which matches Open Library's Knopf record. The publisher's
  and author's pages still don't answer from my network. I also added the
  rule to `CLAUDE.md`: try another reliable source before dropping a book.
- **Hands-On Machine Learning** is now the **PyTorch** book (1st edition,
  O'Reilly, October 2025), because AI Safety research works mostly in PyTorch.
  Verified on the author's page (homl.info: edition 1, released 10-2025, ISBN
  9798341607989) and his repository (chapter list). The print record on Open
  Library has no cover, so `cover_id` comes from the same edition's other
  record; I checked the image. Same `id` as before.
- The Library now has 20 books.

**Stage 5: what I did**
- **Start Here page** (`/start-here/`): stages in order, numbered readings,
  "Why here" note, collapsible synopsis, *To read / Read* buttons with the same
  ids as Papers. There was no provisional route in the repository (it was lost
  with an earlier conversation), so Claude proposed one built from the 12
  verified papers, and re-checked that all 12 original URLs still respond with
  the right title. **The route is not in `papers.yaml` yet:** I review it
  first. Until then the page says the path is being put together.
- **My Own Path page** (`/my-path/`): Timeline (vertical, clickable
  `<details>`, duration bars), Reading log (counters, readings-per-month chart,
  type filter, grouped by month, "via" links to the timeline, archived copies)
  and Bookshelf (reading now / finished, same covers and dialog as the Library).
- **My 14 September readings** in `reading_log.yaml` (all `via: agi-strategy`,
  no notes). None of them is in `papers.yaml`, so none uses `paper_ref`.
- The menu is now News · Papers · Library · Start Here · My Own Path · About.
- The build validates `timeline.yaml`, `reading_log.yaml` and the Start Here
  blocks (section 3.1 of HOW_THIS_SITE_WORKS).

**What I decided and why**
- **`author` is optional in the reading log** when the organisation is the
  author (METR's risk report, Epoch AI's pages). I didn't want to write
  "METR" as an author just to fill a field.
- **Timeline notes with `TODO` are hidden**, like every other placeholder: my
  two course notes are still `TODO(Marco)`, so the stages show without notes.
- **The chart is an HTML list of bars, not a charting library:** one series,
  one colour, the number next to each bar, and every month between the first
  and last shown (an empty month is a visible zero). It works without
  JavaScript and with screen readers, and needs no legend.
- **Books still being read are only on the Bookshelf**, not in the monthly log:
  they have no finished month yet.
- **The Vox article's `archive_url` (archive.ph) can't be checked from here:**
  archive.ph is blocked in Spain (my network redirects it to a Ministry of
  Culture block page), and Claude's own fetcher can't open it either. The
  original Vox URL works (HTTP 200, same headline). I kept the link as given.

**How I tested it**
- Headless Edge against the local preview (19 checks): menu and current page,
  timeline order and bars, no "TODO" on the page, 14 readings, counters, chart,
  type filter (3 resources of 14), via and archive links, no `utm_`; Start
  Here with the proposed route loaded from a temporary copy (4 stages, 12
  readings, a mark set there shows in Papers). No horizontal scroll at 360 px.
- Bookshelf and validation with temporary test data (never in my files): a
  Library book being read, an own finished book with a cover, and the errors
  (finished book without month, unknown `via`, unquoted month, `utm_` URL,
  unknown `paper_ref`, `book_ref` on a non-book). The tests found one real bug
  (a reading without `via` broke the build), now fixed.

**Files created / changed**
Created: `templates/start_here.html`, `templates/my_path.html`. Changed:
`scripts/build_site.py`, `static/css/style.css`, `config/site.yaml`,
`data/books.yaml`, `data/my_path/reading_log.yaml`, `CLAUDE.md`,
`docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Me: approve or correct the Start Here route; then it goes into `papers.yaml`.
- Me: replace the two `TODO(Marco)` timeline notes.
- Check `https://archive.ph/9DCPq` from a network where archive.ph isn't blocked.
- Stage 6: styles (serif, 680px column, light/dark).

---

## 2026-09-23 — Home computer set up and the Start Here path goes in

**What I did**
- I cloned the repository on my home computer, at
  `C:\Users\bymar\Desktop\Varios\Proyectos\AI Safety Web` (a plain local folder,
  not synced by OneDrive). I installed Python 3.12.10 and GitHub CLI 2.101 with
  `winget` (the computer only had Python 3.14), created `.venv` with 3.12,
  installed `requirements.txt` and set the same local Git identity as on my
  work computer. The build ran cleanly before any change.
- I approved the Start Here route that Claude proposed in the previous
  session (with the superlatives toned down) and put it in `data/papers.yaml`:
  four stages in `start_here_stages` and a `start_here` block (stage, order,
  note) on each of the 12 papers.
  1. **Why it matters:** Cotra → AI 2027 → Grace's counterarguments.
  2. **The alignment problem:** Concrete Problems → Ngo et al. → Carlsmith →
     Risks from Learned Optimization (marked optional on a first pass).
  3. **Evidence from today's models:** Sleeper Agents → Alignment Faking.
  4. **What researchers are doing about it:** Model evaluation for extreme
     risks → AI Control → Toy Models of Superposition.

**What I decided and why**
- **Two working copies, two paths:** I work from both computers, so
  `CLAUDE.md` and HOW_THIS_SITE_WORKS §4.2 and §10 now list both folders
  instead of only `C:\dev\AiSafetyWeb`. The rule that matters stays the same:
  never inside a synced folder.
- **Grace right after the case for concern:** the path should let a newcomer
  test the argument, not only absorb it.
- **Every path entry is an existing Papers entry:** I checked that the 12
  titles match the 12 verified entries by `id`, so the path adds no new
  unverified data.
- I added the stages and blocks as text, not by re-saving the YAML with
  PyYAML, so the comments in `papers.yaml` are kept.

**How I tested it**
- The build passes (30 pages, links OK). `start-here/index.html` shows the four
  stages in order with 3, 4, 2 and 3 readings in the approved order, no
  "being put together" message and no `TODO`.
- The live site doesn't exist yet (GitHub Pages comes in Stage 7), so for now
  the path is in the repository and in the local preview.

**Files changed**
`data/papers.yaml`, `CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- ~~Check the Vox article's `archive_url`~~ (done: see the next entry).
- Me: the two `TODO(Marco)` timeline notes (I'll write them later).
- Stage 6: styles.

---

## 2026-09-23 — The Vox article's archived copy moves to the Wayback Machine

**What I did**
- I replaced the `archive_url` of "It's practically impossible to run a big
  AI company ethically" (Vox) in `data/my_path/reading_log.yaml`: from
  `https://archive.ph/9DCPq` to the Wayback Machine copy from 5 August 2024,
  the day it was published
  (`https://web.archive.org/web/20240805132439/https://www.vox.com/future-perfect/364384/its-practically-impossible-to-run-a-big-ai-company-ethically`).
- I added to the "Add a reading to My Own Path" how-to (HOW_THIS_SITE_WORKS §9)
  that archived copies come from the Wayback Machine, not archive.ph.

**What I decided and why**
- **I checked both from my home network.** archive.ph isn't blocked here but
  only answers scripts with a CAPTCHA, so its content couldn't be checked. From
  my work network it redirects to the Ministry of Culture's block page: archive.ph
  is blocked in Spain, so many visitors would never see the copy.
- **The Wayback copy is verified:** it opens (HTTP 200), its headline is the
  same as in my reading log and the article is signed by Sigal Samuel, with
  the full text.

**Files changed**
`data/my_path/reading_log.yaml`, `docs/HOW_THIS_SITE_WORKS.md`, `docs/DEVLOG.md`.

**Pending**
- Stage 6: styles (the e-reader design is approved; applying it next).
- Me: the two `TODO(Marco)` timeline notes.

---

## 2026-09-23 — Stage 6: the e-reader design

**What I did**
- Claude showed me two directions in a throwaway preview (never in the repo):
  a minimal serif design on cream with one green accent, and an
  **e-reader ("Kindle") version**. I chose the e-reader one and discarded the
  first.
- I rewrote `static/css/style.css` around it: Literata as the only typeface,
  sepia paper and ink (near-black paper in dark mode), a 620px column, the
  header centred with the menu in italics, chapter openings (centred title with
  ⁂, drop cap on introductions), Start Here stages as chapters separated by ❦,
  labels in small caps and secondary data in italics.
- I added Literata to the repository (`static/fonts/`: roman and italic
  variable `.woff2`, Latin subset, ~105 KB together) with its licence
  (`static/fonts/Literata-OFL.txt`), and credited it in About.
- New `static/js/theme.js`: a *Dark mode / Light mode* link in the header. A
  short inline script in `base.html` applies the saved choice before the page
  is painted.
- `drop-cap` class in the templates of Start Here, My Own Path, the Library and
  About.

**What I decided and why**
- **Literata, self-hosted, not Google Fonts.** Kindle's own font (Bookerly)
  belongs to Amazon; Literata is the closest free equivalent (made for Google
  Play Books) and is under the SIL Open Font License. Serving it myself means
  visitors' browsers don't contact Google, and it keeps working offline in the
  preview. I checked its authorship and licence in the official repository
  (`github.com/googlefonts/literata`).
- **No colour at all.** Links are ink with an underline, like a book. Because
  that removes the usual colour cue, I made keyboard focus a thick ink ring
  with a paper-coloured gap on everything focusable.
- **Contrast checked, not guessed:** all text pairs pass WCAG AA with room to
  spare (lowest: secondary text on notices, 5.58:1 light / 5.71:1 dark; body
  text ~13–14:1). The table is in HOW_THIS_SITE_WORKS §6.8. Nothing needed
  adjusting. I also dropped the 90% opacity on the typographic covers' author
  line so it keeps full contrast.
- **Justified prose with hyphenation, but not everywhere.** Introductions,
  synopses and About are justified with `hyphens: auto` (the page is
  `lang="en"`, words of 7+ letters only). The tests showed two problems I then
  fixed: the book card's narrow text column opened big gaps (now
  ragged-right), and on phones the hyphenated ragged text had a hyphen every
  other line (now no justification or hyphenation below 34rem). List excerpts
  are never justified: lists must be quick to scan.
- **Drop cap only on pages that open with an introduction.** About's drop cap
  is on its first long paragraph, because the tagline above it is one line.
- **Small caps labels a bit larger than in the mock-up** (1rem instead of
  0.8–0.92rem): in real lists they were too small to read comfortably.

**How I tested it**
- Headless Edge against the local preview, every page in light and dark, at
  desktop width and at 360px (inside 360px frames, because headless Edge won't
  make a window narrower than ~490px): Today, News, a month page, Papers (with
  test marks), the Library with the book card open, Start Here, My Own Path,
  My shelf (with test marks), About and 404. No page scrolls horizontally.
- Keyboard focus on a link, a pressed button, a filter and a book, in both
  themes: the ring is clearly visible.
- The theme toggle, starting from a light and from a dark system: it switches,
  saves the choice and keeps it after a reload.
- Hyphenation: my test browser profile had no English dictionary at first
  (Edge downloads them separately); with the dictionary it hyphenates as
  expected ("read-ings"). Real browsers download it on their own.
- The build still passes with all internal links OK (the font preload and the
  licence link included).

**Files created / changed**
Created: `static/fonts/literata-latin-wght-normal.woff2`,
`static/fonts/literata-latin-wght-italic.woff2`, `static/fonts/Literata-OFL.txt`,
`static/js/theme.js`. Changed: `.gitattributes` (`*.woff2 binary`), `static/css/style.css`, `templates/base.html`,
`templates/about.html`, `templates/start_here.html`, `templates/my_path.html`,
`templates/library.html`, `CLAUDE.md`, `docs/HOW_THIS_SITE_WORKS.md`,
`docs/DEVLOG.md`.

**Pending**
- Stage 7: GitHub Actions workflow and GitHub Pages (and retry Google
  DeepMind's own feed from Actions).
- Stage 8: final documentation review.
- Me: the two `TODO(Marco)` timeline notes.
