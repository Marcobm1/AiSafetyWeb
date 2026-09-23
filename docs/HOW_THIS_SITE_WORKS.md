# How This Site Works

> These are my notes on the **current** state of the project. I update them in
> the same commit as every change. Sections marked **🚧 Not built yet** describe
> the design I agreed on for a future stage.
>
> I wrote them for someone with a technical background (my own is security
> operations) who is new to web development. Unfamiliar terms are defined in the
> [Glossary](#glossary).

**Current status:** Stages 1–8 built and **published at https://marcobm1.github.io/AiSafetyWeb/**: news, Papers, the Library, Start Here (12 papers in 4 stages), My Own Path v2 (Timeline, Bookshelf and a monthly Journal, plus my local-only "Add entry" form) and My shelf, with the e-reader design (Literata, sepia paper, light and dark). A GitHub Actions workflow updates the data every day at 06:00 UTC and redeploys the site (section 7). Next: Stage 9 (final documentation review). The plan for the remaining stages is in [docs/DEVLOG.md](DEVLOG.md).

## Contents
1. [What this project is](#1-what-this-project-is)
2. [Architecture](#2-architecture)
3. [Folders and files](#3-folders-and-files)
4. [Setting up a computer](#4-setting-up-a-computer)
5. [The fetch script, step by step](#5-the-fetch-script-step-by-step)
6. [Building and previewing the site locally](#6-building-and-previewing-the-site-locally)
7. [GitHub Actions and the cron schedule](#7-github-actions-and-the-cron-schedule)
8. [Deployment to GitHub Pages and the base path](#8-deployment-to-github-pages-and-the-base-path)
9. [How to…](#9-how-to)
10. [Working from two computers](#10-working-from-two-computers)
11. [Common problems and fixes](#11-common-problems-and-fixes)
12. [Possible future extensions](#12-possible-future-extensions)
13. [Glossary](#glossary)

---

## 1. What this project is

I built a **static website** about AI Safety, hosted for free on **GitHub Pages**
at https://marcobm1.github.io/AiSafetyWeb/. It has:

| Section | What it shows | Where the data comes from |
|---|---|---|
| **Today in AI Safety** (home) | Entries from the last 24–48 h, grouped by topic/source | Collected automatically every day |
| **News archive** | All earlier entries, browsable by date, filterable by source/topic | Same automatic collection |
| **Papers** | My curated list of papers, essays, reports, scenarios and posts, each with a short synopsis, filterable by year, type, topic and difficulty | `data/papers.yaml`, which I edit by hand |
| **Library** | Books only, on six themed shelves, each shown with its real cover (Open Library) or a typographic one. Clicking a book opens its card; each book also has its own page | `data/books.yaml`, which I edit by hand |
| **Start Here** | An ordered reading path for newcomers to AI Safety, in stages, each entry with a note on why it sits at that point (4 stages, 12 readings from Papers) | Also `data/papers.yaml`: the stage list plus a `start_here` block on each entry in the path |
| **My Own Path** | My public learning log: a **Timeline** of courses, projects and milestones (with duration bars), a **Bookshelf** of the books I read, with my opinion, and a **Journal**: one month at a time (month selector), everything I did that month grouped by type, with an activity-per-month chart | `data/my_path/timeline.yaml` and `data/my_path/reading_log.yaml`, which I edit by hand or with my local "Add entry" form |
| **Reading tracker** | Each visitor marks entries as *To read* / *Read* (in Papers, the Library and Start Here) | The visitor's own browser (localStorage) |
| **My shelf** | The visitor's own marks in one page, with **Export / Import** to back them up or move them to another browser | The visitor's own browser (localStorage) |
| **About** | What the site is, sources, how updates work, the typeface credit and a note that it was built with the help of Claude Code | Template text |

**My shelf vs My Own Path:** My shelf (the reading tracker) is private to each
visitor's browser and nobody else sees it; there are no accounts. My Own Path
is my own *public* record, written by me in files in the repository.

My content rules: the site only shows the **title, source, date, a short excerpt
(max ~2 sentences) and a link** to each original. I never republish full
articles. Each entry has an empty `summary` field that I'm reserving for future
AI summaries.

## 2. Architecture

There is **no server and no database**. Everything is files in the Git repository.
A robot (GitHub Actions) runs once a day, adds new data, rebuilds the HTML and
publishes it.

```mermaid
flowchart LR
    subgraph Sources["External sources"]
        RSS["RSS/Atom feeds<br/>(LessWrong, Alignment Forum, blogs...)"]
        ARX["arXiv API"]
    end

    subgraph Actions["GitHub Actions (daily cron)"]
        F["scripts/fetch_news.py"]
        B["scripts/build_site.py"]
    end

    subgraph Repo["Git repository"]
        CFG["config/sources.yaml"]
        NEWS["data/news/YYYY-MM.json"]
        CAND["data/paper_candidates.json<br/>(auto-pruned)"]
        PAP["data/papers.yaml + data/books.yaml<br/>(edited by hand)"]
        PATH["data/my_path/<br/>timeline + reading log<br/>(edited by hand)"]
        TPL["templates/ + static/"]
    end

    RSS --> F
    ARX --> F
    CFG --> F
    F -->|"new entries, commit"| NEWS
    F -->|"new arXiv papers"| CAND
    CAND -.->|"I promote one<br/>(promote_candidate.py)"| PAP
    NEWS --> B
    PAP --> B
    PATH --> B
    TPL --> B
    B -->|"_site/ (HTML, CSS, JS)"| PAGES["GitHub Pages<br/>marcobm1.github.io/AiSafetyWeb/"]
    PAGES --> V["Visitor's browser<br/>(My shelf marks in localStorage)"]
```

**Why I chose Python + Jinja2 instead of a site generator like Astro or Eleventy:**
the fetch script has to be Python anyway. Writing the page generator in Python
too means I only deal with one language and toolchain (no Node.js/npm), and
Python is also the language I use for ML. The generated HTML is complete on its
own, so the site works without JavaScript. JavaScript only adds filters, the
dark-mode toggle and the reading tracker (My shelf).

## 3. Folders and files

| Path | Purpose | Status |
|---|---|---|
| `CLAUDE.md` | Permanent rules for Claude sessions working on this repo | ✅ |
| `README.md` | Short intro and quick start | ✅ |
| `requirements.txt` | Python dependencies with **pinned** (exact) versions | ✅ |
| `.python-version` | The Python version (3.12). GitHub Actions reads this file too | ✅ |
| `.gitignore` | Files Git must ignore (`.venv/`, `_site/`, caches) | ✅ |
| `.gitattributes` | Forces LF line endings in the repo (avoids Windows/Linux diffs) | ✅ |
| `docs/HOW_THIS_SITE_WORKS.md` | These notes | ✅ |
| `docs/DEVLOG.md` | My chronological log of every change and why | ✅ |
| `config/sources.yaml` | All news sources, arXiv query, karma thresholds, topic keywords | ✅ |
| `config/site.yaml` | Site title, base path, home-page window, topic labels, menu | ✅ |
| `scripts/fetch_news.py` | Downloads feeds + arXiv, deduplicates, saves JSON and paper candidates | ✅ |
| `data/news/YYYY-MM.json` | Collected news, one file per month | ✅ |
| `data/status.json` | Time of last run + status of each source | ✅ |
| `data/paper_candidates.json` | New arXiv papers I might add to the archive. Written by the bot, old ones pruned automatically | ✅ |
| `data/papers.yaml` | Papers: my curated papers, essays, reports, scenarios and posts (13 so far); also the Start Here stage list | ✅ |
| `data/books.yaml` | Library: 20 books on six themed shelves | ✅ |
| `data/my_path/timeline.yaml` | My Own Path timeline (my first two courses) | ✅ |
| `data/my_path/reading_log.yaml` | My Own Path readings and resources (my 14 September readings); shown in the Journal | ✅ |
| `scripts/local_form.py` | The local-only "Add entry" form, served by `build_site.py --serve` (section 6.9) | ✅ |
| `templates/local/add_entry.html` | The form's page; only ever rendered by the preview server, never into `_site/` | ✅ |
| `scripts/promote_candidate.py` | Copies a candidate into `papers.yaml` as a new block | ✅ |
| `scripts/build_site.py` | Turns templates + data into the `_site/` folder, checks links, local preview | ✅ |
| `templates/` | Jinja2 HTML templates (`base.html`, `_macros.html`, one per page type) | ✅ (more pages in Stages 4–5) |
| `static/css/style.css` | The whole design: colour tokens, light/dark, typography, layout (section 6.8) | ✅ |
| `static/fonts/` | Literata (two `.woff2` files, roman and italic) and its licence `Literata-OFL.txt` | ✅ |
| `static/js/theme.js` | The *Dark mode / Light mode* toggle in the header | ✅ |
| `static/js/journal.js` | My Own Path Journal: month selector, Older / Newer, month in the URL | ✅ |
| `static/js/filters.js` | Filter menus for news and papers | ✅ |
| `static/js/reading-store.js`, `tracker.js`, `my-shelf.js` | Reading tracker: the `ReadingStore`, the *To read / Read* buttons, the My shelf page with export/import | ✅ |
| `static/js/library.js` | Library: cover fallback, reading marks on the shelves, the book card `<dialog>` | ✅ |
| `.github/workflows/update-and-deploy.yml` | The one workflow: daily fetch + commit, build, deploy to GitHub Pages (section 7) | ✅ |
| `static/js/stale.js` | The "This site may be out of date" warning, checked in the visitor's browser | ✅ |
| `_site/` | Generated website. **Not committed**, rebuilt each time | ✅ |
| `.venv/` | Python virtual environment. **Not committed**, one per computer | ✅ (local) |

**Why one JSON file per month:** the files stay small, the daily Git diffs stay
readable, and merge conflicts are rare because only the current month's file changes.

**YAML for what I edit, JSON for what the bot writes:** YAML is easier for me
to read and edit by hand, and it allows comments. JSON is strict, which is
safer for files that a script rewrites every day.

### 3.1 Data formats

I fixed these formats in Stage 2, even though the Library, Start Here and My
Own Path pages come later, so every script and page is built against the same shape.

**The `id` is the glue.** Every entry in `papers.yaml` and `books.yaml` has a
stable `id` (a short lowercase slug such as `ai-2027` or `sleeper-agents`),
**unique across both files**. Papers, the Library, the Start Here path, the My
Own Path reading log and the visitors' reading tracker all refer to an entry
by this `id`, so its data (title, authors, URL) lives in one place only. **I
never change an `id` once it's published**, because visitors' saved *To read /
Read* marks point to it. The build fails if the same `id` appears twice.

**Why books and papers are separate:** they are read and browsed differently.
Papers are best as a filterable list with a synopsis; books are nicer as
shelves of covers you can pick up. They also need different fields (edition,
cover, shelf). Two files keep each format simple, and the shared `id` rule
keeps the tracker working across both.

**The publishing rule (both files).** An entry is published only when it has a
`synopsis` without `TODO`: 2–4 neutral sentences, based on the verified
source, never copied from the publisher, Amazon, Goodreads, reviews or the
abstract. `why_it_matters` and `my_opinion` are optional and only appear when
they exist. **`my_opinion` is only ever written by me**; Claude may draft a
synopsis, never my opinion. An entry with no synopsis, or with a `TODO` in a
required field, is skipped by the build with a warning, so a half-finished
entry never goes live.

#### `data/papers.yaml` — Papers (edited by hand)

The file has two top-level keys. `start_here_stages` lists the stages of the
Start Here path, in the order they appear on the site. `entries` holds every
paper, essay, report, scenario and post. **`entries` must stay the last key in
the file**, because `promote_candidate.py` appends new entries to the end of
the file.

```yaml
start_here_stages:                     # order in this list = order on the site
  - id: why-it-matters                 # referenced by start_here.stage below
    title: Why it matters
    intro: >
      Short paragraph shown at the top of the stage.

entries:
  - id: sleeper-agents                 # stable slug, unique, never changes
    title: "Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training"
    authors: ["Evan Hubinger", "Carson Denison", "Jesse Mu", "et al."] # "et al." for long lists
    year: 2024
    type: paper                        # paper | essay | report | scenario | blog-post
    url: https://arxiv.org/abs/2401.05566
    arxiv_id: "2401.05566"             # optional; lets the fetch script skip it as a candidate
    tags: [alignment, evals]           # topics: alignment | interpretability | evals | governance | security
    difficulty: intermediate           # intro | intermediate | advanced
    synopsis: >                        # REQUIRED to publish: 2-4 neutral sentences
      What the text says, in my own words.
    why_it_matters: >                  # optional
      Why it is in this list.
    my_opinion: >                      # optional, only mine
      What I think of it.
    added: 2026-09-23                  # date I added it
    start_here:                        # optional: only if it's part of the Start Here path
      stage: evaluations               # an id from start_here_stages
      order: 2                         # position inside that stage
      note: >
        Why it sits at this point of the path.
```

The website shows `type` and `difficulty` as labels and the tags as topics,
and lets visitors filter by year, type, topic and difficulty. The build checks
every published entry and stops with a clear message if something is wrong:
a required field missing, an `id` that isn't a lowercase slug, an unknown
`type`, `difficulty` or topic (topics must be the five ids in
`config/sources.yaml`), a URL that isn't http(s) or has `utm_` parameters, or a
`start_here.stage` that isn't in `start_here_stages`.

#### `data/books.yaml` — the Library (edited by hand)

Two top-level keys: `shelves` (id and title, in the order they appear on the
site) and `entries` (the books).

```yaml
shelves:                               # order in this list = order on the site
  - id: ai-safety                      # referenced by `shelf` below
    title: AI Safety & Alignment

entries:
  - id: human-compatible               # unique across papers.yaml and books.yaml
    title: "Human Compatible"
    subtitle: "Artificial Intelligence and the Problem of Control"   # optional
    authors: ["Stuart Russell"]
    edition: "3rd edition"             # optional: only for numbered editions
    year: 2019                         # year of THIS edition
    publisher: "Viking"
    shelf: ai-safety                   # an id from `shelves`
    olid: OL27724147M                  # Open Library EDITION id (OL...M)
    cover_id: 13157736                 # optional: Open Library cover id
    isbn: "9780525558613"              # optional, reference only (never used to load covers)
    url: https://openlibrary.org/books/OL27724147M   # the "Book page on Open Library" link
    free_url: https://...              # optional: ONLY an official free version
    synopsis: >                        # REQUIRED to publish
      ...
    why_it_matters: >                  # optional
      ...
    my_opinion: >                      # optional, only mine
      ...
    added: 2026-09-23
```

- **Edition:** always the most recent English edition. A new numbered or
  revised edition counts (Axler's 4th); a paperback reprint of the same text
  doesn't. `year` is the year of the edition I list. For Géron I list the 2025
  *…with Scikit-Learn and PyTorch* (a new book, 1st edition) instead of the
  TensorFlow one, because AI Safety research works mostly in PyTorch.
- **Verification:** title, subtitle, authors, publisher and year against the
  publisher's or author's page, or another reliable source when those pages
  can't be reached from my network (Wikipedia, WorldCat, or an archived copy
  of the official page on the Wayback Machine); the OLID, cover id and ISBN on
  Open Library. A book I can't check against any reliable source stays out.
- **One edition, two Open Library records:** sometimes the print edition's
  record has no cover but the ebook record of the same edition has one (Géron's
  PyTorch book). Then `olid` and `isbn` are the print edition's and `cover_id`
  comes from the other record, with a comment saying so.
- **Covers** come straight from Open Library's Covers API as the image `src`:
  `https://covers.openlibrary.org/b/id/<cover_id>-M.jpg` on the shelf and
  `-L.jpg` in the card. I never download them into the repo. I only use the
  **cover id**, never the ISBN, because ISBN lookups are limited to 100
  requests every 5 minutes per IP address. A book without `cover_id` gets a
  **typographic cover** (title and author on a colour per shelf); the same
  cover sits under every image, so it also shows if an image fails to load.
  The Library page, each book page and About credit Open Library.
- **`free_url`** is shown as "Free version (official)". Only for versions the
  authors or publisher publish for free themselves (for example
  deeplearningbook.org, Axler's open-access 4th edition, or
  probabilitybook.net, which Harvard's Stat 110 course page names as the free
  online version of Blitzstein & Hwang), never unauthorised copies.
- **The build checks** (and stops with a clear message otherwise): required
  fields, a slug `id`, a `shelf` from `shelves`, an `olid` like `OL…M`, a
  numeric `cover_id`, http(s) URLs without `utm_`, and ids unique across
  `papers.yaml` and `books.yaml`. Books without a synopsis are skipped with a
  warning, like papers.
- **Shelves:** AI Safety & Alignment; AI, Society & Governance; Machine
  Learning & Deep Learning; Mathematics for ML; Programming & Python; Thinking &
  Rationality. *AI Snake Oil* sits on the first one on purpose, as a sceptical
  counterpoint.

**Why Start Here has no file of its own:** a reading joins the path through its
own `start_here` block, so its data exists only once and the path can never
point to an entry that isn't in the Library. The build script groups the
entries by `start_here.stage` and sorts them by `start_here.order`; the stage
titles and intros come from `start_here_stages`. The build fails with a clear
message if an entry names a stage that isn't in that list.

#### `data/news/YYYY-MM.json` — collected news (written by the bot)

A JSON list, newest first. An entry goes into the file of the month it was
**published** (not the month it was fetched).

```json
[
  {
    "id": "ad56e86e1a6694f2",
    "url": "https://www.lesswrong.com/posts/HsijShdRdAg5sPKnF/an-unexamined-cause-...",
    "title": "An unexamined cause of the OpenAI Hugging Face hacking incident: ...",
    "source": "LessWrong",
    "source_id": "lesswrong",
    "published": "2026-09-23T03:20:03Z",
    "fetched_at": "2026-09-23T10:45:44Z",
    "excerpt": "At most two sentences, HTML removed, max 320 characters.",
    "topics": ["alignment", "evals"],
    "summary": null
  }
]
```

- `id`: the first 16 characters of the SHA-1 hash of the normalised URL, so the
  same URL always gets the same id.
- `source` is the label shown on the site; `source_id` matches the source's
  `id` in `config/sources.yaml` and in `status.json`.
- arXiv entries also have `authors` (list) and `arxiv_id`.
- Times are always **UTC** in ISO 8601 format (the `Z` at the end means UTC).
- `summary` is always `null` for now: reserved for future AI summaries.

#### `data/status.json` — what happened in the last run (written by the bot)

```json
{
  "last_run": "2026-09-23T10:45:44Z",
  "duration_seconds": 15.9,
  "new_entries": 137,
  "sources": [
    {"id": "lesswrong", "name": "LessWrong", "status": "ok",
     "items_in_feed": 10, "kept": 6, "new": 6, "error": null}
  ],
  "candidates": {"added": 100, "removed_promoted": 0, "pruned": 0, "total": 100}
}
```

Per source: `items_in_feed` is what the feed returned, `kept` is what passed
the filters (age, topic), `new` is what wasn't already saved. When a source
fails, `status` is `"error"` and `error` says why. The site will use
`last_run` for its "This site may be out of date" warning (section 7.4).

#### `data/paper_candidates.json` — arXiv papers I might curate (written by the bot)

```json
{
  "arxiv:2401.05566": {
    "id": "arxiv:2401.05566",
    "title": "Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training",
    "authors": ["Evan Hubinger", "Carson Denison", "..."],
    "year": 2024,
    "url": "https://arxiv.org/abs/2401.05566",
    "abstract": "First two sentences of the abstract at most.",
    "detected": "2026-09-23",
    "topics": ["alignment", "evals"]
  }
}
```

- The `id` is `arxiv:` + the arXiv number **without** the version suffix
  (`v1`, `v2`…), so a new version of the same paper never creates a duplicate.
- A paper is **not** added if it's already a candidate or already in
  `papers.yaml` (matched by `arxiv_id` or by its normalised arXiv URL).
- Candidates older than `candidates.retention_days` (in `config/sources.yaml`,
  default 60 days) are deleted on every run, so the file never grows without limit.
- A candidate I have promoted to `papers.yaml` is removed on the next run.
- Only papers that are **new to the news files** become candidates. That way a
  candidate I let expire never comes back just because arXiv still lists it.

#### `data/my_path/` — My Own Path (edited by hand or with my local form)

My Own Path has two parts, each in its own file:

**`timeline.yaml` — courses, projects and milestones**

```yaml
- id: future-of-ai              # stable slug; reading-log entries point to it with `via`
  type: course                  # course | project | milestone
  date: 2026-09-07              # when I started (or when it happened, for a milestone)
  completed: 2026-09-11         # optional: when I finished; left out while in progress
  title: Future of AI
  provider: BlueDot Impact      # optional
  url: https://bluedot.org/courses/future-of-ai   # optional
  status: completed             # in-progress | completed
  notes: >                      # optional: my takeaways, in first person
    ...
```

**`reading_log.yaml` — everything I read**

```yaml
entries:
  - month: "2026-09"            # month only (quoted, so YAML keeps it as text)
    type: essay                 # paper | report | essay | article | book | resource | podcast-video
    title: "Exact title"
    author: "Author Name"
    source: "Cold Takes"        # publication or website
    url: https://...            # the original, without utm_ parameters
    archive_url: https://...    # optional: archived copy of a paywalled article
    via: agi-strategy           # optional: the Timeline stage I read it in
    notes: >                    # optional
      ...

  - month: "2026-09"
    type: paper
    paper_ref: sleeper-agents   # already in Papers: title, author, source
    via: agi-strategy           # and URL come from papers.yaml

  - type: book                  # a book I'm still reading
    status: reading             # books only: reading | finished
    started: "2026-09"          # books only, optional
    book_ref: human-compatible  # (illustrative) already in the Library

  - month: "2026-10"            # for a book: the month I FINISHED it
    type: book
    status: finished
    title: "A novel I don't want in the public Library"
    author: "Author Name"
    source: "Publisher"
    url: https://openlibrary.org/works/...
    cover_id: 1234567           # optional, for the cover on my Bookshelf
    notes: >
      My opinion, because this book is not in books.yaml.
```

- **`paper_ref` / `book_ref`** replace the old `library_ref`: a reading that is
  already in Papers or the Library points to it by `id` instead of copying its
  data.
- **Books** can take several months, so they have `status` (reading /
  finished), an optional `started` month and `month` = the month I finished
  (left out while reading). On My Own Path they appear on a **Bookshelf**
  (same shelf style and book card as the Library, Stage 5).
- **Where my opinion lives:** in `my_opinion` in `papers.yaml` / `books.yaml`
  when the reading is there (so the Library and my Bookshelf show the same
  text); `notes` in the reading log only for readings that are *not* in Papers
  or the Library. A book I don't want in the public Library goes here with its
  own data and no `book_ref`.

- **`author` is optional** when the organisation itself is the author (METR's
  risk report, Epoch AI's data pages): then the site shows only `source`.

- **`podcast-video`** (shown as "Podcast / video") is for things I watch or
  listen to: a talk, an interview, a podcast episode. One type for both,
  because what matters in my log is that it wasn't a text.

Rules the build script checks, failing with a clear message: `type` must be
one of the seven types; `month` must be a quoted `"YYYY-MM"`; `via` must be an
`id` in `timeline.yaml`; `paper_ref` must be a published entry of
`papers.yaml` and `book_ref` a published book of `books.yaml` (and only on
`type: book`; never both); a book needs `status`, a finished book needs
`month`, a book I'm still reading has no `month`, and `started` can't be after
`month`; `status` / `started` / `cover_id` only on books; an entry without a
ref needs `title`, `source` and `url`; no URL may contain `utm_` parameters.

For the **timeline**, the build checks the `id` (unique slug), `type`,
`status`, the dates (`completed` not before `date`; a completed course or
project needs `completed`; a stage with `completed` must have
`status: completed`) and URLs.

The rules live in two functions in `build_site.py`, `check_timeline_item` and
`check_log_entry`. The build and the local "Add entry" form (section 6.9) call
the same functions, so the form can never accept something the build would
reject. **Notes that still contain `TODO` are not
shown**, so placeholders like my `TODO(Marco)` notes never go live.

#### The visitor's marks (localStorage, never in the repo)

The reading tracker saves one small JSON value in the visitor's browser, under
the key `aisafetyweb.reading.v1`:

```json
{"version": 1, "items": {"sleeper-agents": {"status": "read", "updated": "2026-09-23T10:00:00.000Z"}}}
```

`status` is `to-read` or `read`; there is no entry for unmarked readings. The
**export** file has the same `items` plus a header:
`{"format": "aisafetyweb-reading", "version": 1, "exported": "...", "items": {...}}`.

**Why two files instead of one `my_path.yaml` with two sections:**
- They grow very differently. The timeline gets a new stage every few weeks;
  the reading log gets entries every week. Keeping the long list apart means
  the short one stays easy to read and edit.
- Different shapes (days vs months, different fields and types). A separate
  file per shape keeps each file's header comment and template short and exact.
- Fewer indentation mistakes: a slip in a long YAML file can silently move an
  entry into the wrong section; with two files it can't cross over.
- Clearer Git history: "added 3 readings" and "finished a course" show up as
  changes to different files.
- The folder `data/my_path/` still keeps both halves of the section together.

**How I write these docs:** every Markdown file meant for readers (`README.md`,
everything in `docs/`) is written in first person, as my own technical notes,
in English. `CLAUDE.md` is the exception: it holds instructions for Claude, and
this style rule is recorded there so every session follows it.

## 4. Setting up a computer

### 4.1 Tools
I install these once per computer (Windows, PowerShell):

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id GitHub.cli -e
```

Then I close and reopen the terminal so the new commands are found, and check:
`git --version`, `py -3.12 --version`, `gh --version`.

### 4.2 Location: never inside OneDrive
On my work computer I keep the project at **`C:\dev\AiSafetyWeb`**; on my home
computer it lives at **`C:\Users\bymar\Desktop\Varios\Proyectos\AI Safety Web`**
(my Desktop there is a normal local folder, not synced by OneDrive). Any local
path works as long as no sync tool watches it. OneDrive (and similar sync tools)
upload and rewrite files inside the hidden `.git/` folder while Git is using
them. That can corrupt the repository or create "conflicted copy" files. GitHub
is already the synchronisation mechanism between my computers.

### 4.3 Authenticate Git with GitHub
```powershell
gh auth login
```
I choose: **GitHub.com** → **HTTPS** → **Yes** (authenticate Git with my GitHub
credentials) → **Login with a web browser**. I copy the one-time code shown,
press Enter, paste the code in the browser and approve. I check it worked with
`gh auth status`.

### 4.4 Git identity: local vs global configuration
Every commit records an author name and email. Git reads these settings from
three levels, and the most specific one wins:

| Level | Command | Stored in | Applies to |
|---|---|---|---|
| system | `git config --system` | Git installation folder | All users of the computer |
| **global** | `git config --global` | `C:\Users\<me>\.gitconfig` | All my repositories |
| **local** | `git config --local` | `<repo>\.git\config` | **Only this repository** |

I use **local** settings for this project, so they don't affect my other
repositories (for example, work ones that need a different identity):

```powershell
cd C:\dev\AiSafetyWeb
git config --local user.name "Marco Barrera Martín"
git config --local user.email "87645460+Marcobm1@users.noreply.github.com"
git config --local --list      # check
```

The email is GitHub's private **noreply** address (GitHub → Settings → Emails).
The repository is public and every commit shows its author email, so this
address keeps my real email private. Local settings live inside `.git/`,
which is not pushed, so **I have to run these commands on each computer**.

### 4.5 Python virtual environment (venv)
A **virtual environment** is a private folder (`.venv/`) holding the Python
packages for this project only. It stops these packages from clashing with my
other Python projects. It is not committed; each computer creates its own from
`requirements.txt`.

```powershell
cd C:\dev\AiSafetyWeb
py -3.12 -m venv .venv                 # create (once per computer)
.\.venv\Scripts\Activate.ps1           # activate (every new terminal)
pip install -r requirements.txt        # install pinned packages
deactivate                             # leave the venv (optional)
```

When the venv is active, the prompt starts with `(.venv)` and `python` means the
project's Python 3.12.

If `Activate.ps1` is blocked with *"running scripts is disabled on this system"*,
I run this once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. If a
company policy forbids it, I skip activation and call the venv's Python directly:
`.\.venv\Scripts\python.exe scripts\build_site.py`.

**Same Python everywhere:** `.python-version` says `3.12`. I create the local
venv with `py -3.12`, and the GitHub Actions workflow reads the same file.

## 5. The fetch script, step by step

✅ **Built in Stage 2.** The script is `scripts/fetch_news.py` and all its
settings live in `config/sources.yaml`. I run it from the repository root
with the venv active:

```powershell
python scripts\fetch_news.py            # fetch and save
python scripts\fetch_news.py --dry-run  # fetch and report, but write nothing
```

It prints one line per source (`ok` or `ERROR`, how many items the feed had
and how many it kept) and a summary at the end. A full run takes ~15 seconds.

### 5.1 What one run does

1. **Read `config/sources.yaml`.** All sources, the arXiv query, the karma
   thresholds and the topic keywords are in this one file.
2. **Download every RSS/Atom feed.** Each download has a 30-second timeout and
   one retry. If a source still fails, the error is recorded in `status.json`
   and **the other sources carry on**.
   - LessWrong and the Alignment Forum filter by karma on their side: the
     script adds `karmaThreshold=30` (LessWrong) or `karmaThreshold=20` (AF) to
     the feed URL, so only posts that reached that karma come back.
3. **Ask the arXiv API** once for the 100 newest papers in cs.AI, cs.LG or
   cs.CL whose title or abstract contains one of the phrases in
   `arxiv.phrases`, or all the terms of one entry in `arxiv.combinations`
   (e.g. *interpretability* **and** *deception*). One request a day is far
   below arXiv's limits. If a download fails, it retries once; if the server
   answers **429 Too Many Requests** or **503**, it waits as long as the
   server's `Retry-After` header says (at least 30 s) before retrying.
4. **Turn every item into an entry** (format in section 3.1):
   - remove HTML, keep at most **two sentences / 320 characters** as the
     excerpt (the site never republishes full articles);
   - **drop items older than 14 days** (`settings.max_age_days`). Some feeds
     return their whole history (OpenAI's has 1,000+ items), and I don't want
     to import years of old posts;
   - **assign topics** by keyword (section 5.2);
   - for sources marked `require_topic: true`, **drop items that match no
     topic**. I use this for sources that also publish off-topic things
     (LessWrong, OpenAI, Google DeepMind, GovAI's job postings…).
5. **Skip duplicates.** Before comparing, every URL is **normalised**: https,
   lowercase host, no `utm_*` tracking parameters, no trailing slash, and arXiv
   `/pdf/…v2` links turned into `/abs/<id>`. LessWrong and the Alignment Forum
   share posts, so for them the post id is compared instead.

   As a second check, the **title** (lowercase, punctuation removed) is
   compared, but **only between two different sources marked
   `crossposts: true`** in `config/sources.yaml`. Those are sources I have
   *seen* publish the same post under different URLs: the Alignment Forum,
   LessWrong, Redwood Research (its posts also go to the AF) and METR (one joint
   investigation appeared on both METR's and Redwood's blogs). Titles shorter
   than 4 words are never compared. The first source in the config keeps the
   item, which is why the Alignment Forum is listed first.

   Why so narrow: comparing titles across *all* sources would merge unrelated
   posts with generic titles ("Weekly update on AI safety research") from two
   different blogs, and even two different pages of one source (OpenAI has two
   pages called "The state of enterprise AI"). I also tried "same title **and**
   same author", but it misses every real cross-post: the AF shows the
   username (`Jozdien`, `ryan_greenblatt`) while Redwood's blog shows the real
   name or a different co-author (`Arun Jose`, `Nathan Sheffield`).

   Measured on 2026-09-23: the rule finds the 3 Redwood/AF duplicates in the
   Stage 2 data, 0 in the current news file, and 4 in the full current feeds
   (1,611 items without any filter): those 3 plus the METR/Redwood joint post.
   No false positives. **To mark a new source**, I add `crossposts: true` only
   after seeing a real cross-post in the data.
6. **Save** new entries into `data/news/YYYY-MM.json` by publication month.
   arXiv papers go there too, so they appear on the home page like any other news.
7. **Update the paper candidates** (`data/paper_candidates.json`): add the new
   arXiv papers that aren't in `papers.yaml`, remove those I've promoted, and
   delete those older than `candidates.retention_days` (60). Candidates are
   **not** shown on the website; they are my shortlist in the repository (which
   is public, but nobody browses it like the site).
8. **Write `data/status.json` on every run**, even when nothing is new. Because
   `last_run` changes every time, the daily bot always has something to commit,
   and that keeps the repository "active" for GitHub (section 7).

Files are written **atomically**: first to a `.tmp` file, then renamed over
the real one, so a crash halfway never leaves a half-written JSON file.

**Exit code:** the script ends with an error (exit code 1) only if **every**
source failed. That usually means a problem on my side (no network, broken
config), and I want GitHub Actions to mark the run as failed and email me. One
broken feed is normal and only shows up in `status.json`.

### 5.2 Topics and keywords

There are five topics: **alignment, interpretability, evals, governance,
security**. Each has a keyword list in `config/sources.yaml`. The script looks
for them in the title and the first 600 characters of the text (LessWrong
feeds contain the whole post, and a long post mentions every topic in passing).

- Matching is **case insensitive** and on **whole words**: `AGI` does not
  match "agile".
- A trailing `*` allows any ending: `misalign*` matches "misaligned" and
  "misalignment".
- An entry can have several topics, or none.

Keyword matching is simple and imperfect (a paper on "image-text alignment"
counts as *alignment*). It's good enough for filtering and grouping; I can
refine the lists at any time.

### 5.3 The sources (checked 2026-09-23)

| id | Source | Filter |
|---|---|---|
| `alignment-forum` | AI Alignment Forum | karma ≥ 20 |
| `transformer-circuits` | Transformer Circuits Thread (Anthropic's interpretability research) | always tagged *interpretability* |
| `lesswrong` | LessWrong | karma ≥ 30, on-topic only |
| `ai-safety-newsletter` | AI Safety Newsletter (CAIS; its Substack, on the `newsletter.safe.ai` domain) | — |
| `metr` | METR | — |
| `redwood` | Redwood Research | — |
| `govai` | Centre for the Governance of AI | on-topic only |
| `transformer` | Transformer | on-topic only |
| `import-ai` | Import AI | — |
| `zvi` | Don't Worry About the Vase | on-topic only |
| `epoch` | Epoch AI | on-topic only |
| `bluedot` | BlueDot Impact | on-topic only |
| `openai` | OpenAI News | on-topic only |
| `google-deepmind` | Google DeepMind | on-topic only |
| `arxiv` | arXiv API (cs.AI, cs.LG, cs.CL) | phrase + combination query (section 5.4) |

Every URL was checked (HTTP 200 + a valid feed) before adding it.

- **No feed, so left out:** Anthropic's news page and its **Alignment Science
  blog** (`alignment.anthropic.com`: no `<link rel="alternate">`, and `/feed`,
  `/feed.xml`, `/rss.xml`, `/atom.xml`, `/index.xml` all return 404), Apollo
  Research, the UK AI Security Institute and the CAIS blog (CAIS is covered by
  its newsletter). Anthropic's **interpretability** research *does* have a feed
  (Transformer Circuits Thread), so that one is in.
- **Google DeepMind:** I use its own feed, `deepmind.google/blog/rss.xml`. It
  fails from my work network (TLS handshake blocked), so until Stage 8 I used
  the one on `blog.google`. In Stage 8 I tested it from GitHub Actions
  (`--check-feed`: 100 items, OK) and from home: it has five times as many
  items as `blog.google`'s DeepMind category and includes DeepMind-only posts
  that `blog.google` leaves out, so I switched. From my work computer the
  `--dry-run` will show this one source as failing; that's expected, the daily
  run happens on GitHub's servers.
- **Substack blocks GitHub's servers (found in Stage 8).** The four sources on
  `*.substack.com` (Redwood Research, Import AI, Zvi, Epoch AI) answer
  **403 Forbidden** to GitHub Actions, while from my home network, with the
  same User-Agent, they work: Substack refuses requests from data-centre
  addresses. Substack newsletters on their own domain (CAIS's
  `newsletter.safe.ai`, Transformer) are not affected. Until I decide how to
  replace them (see DEVLOG), those four show as failing in `status.json` and
  on About, and the daily run carries on without them.
- **`default_topics`:** a source can add fixed topics to all its entries. I use
  it for Transformer Circuits, whose titles ("HeadVis") often contain no keyword.

### 5.4 The arXiv query and why "interpretability" is combined

arXiv's search matches word **stems**: "interpretability" also finds
"interpretable" and "interpretation". I measured one week (2026-09-15 to 22) in
cs.AI/cs.LG/cs.CL, titles and abstracts:

| Query | Papers/week | Quality |
|---|---|---|
| interpretability (alone) | 195 | mostly generic explainability |
| interpretability AND safety | 12 | mostly noise (medical, legal…) |
| interpretability AND alignment | 33 | noise ("cross-modal alignment"…) |
| "mechanistic interpretability" | 6 | relevant |
| interpretability AND ("AI safety" or "AI alignment") | 1 | relevant |
| interpretability AND (deception or deceptive) | 4 | about half relevant |

So I keep "mechanistic interpretability" and "sparse autoencoder" as phrases
and add the precise combinations under `arxiv.combinations`. The whole query
went from 71 to 74 papers a week: most interpretability-and-safety papers were
already caught by other phrases.

## 6. Building and previewing the site locally

✅ **Built in Stage 3.** The generator is `scripts/build_site.py`. It reads
`config/site.yaml`, `config/sources.yaml` and the data files (news, status,
`papers.yaml`), and writes the
finished website into `_site/` (never committed; it's rebuilt every time).

```powershell
python scripts\build_site.py                  # build into _site\
python scripts\build_site.py --serve          # build, then preview
python scripts\build_site.py --serve --port 8001   # if port 8000 is busy
```

With `--serve` I open **http://localhost:8000/AiSafetyWeb/** and stop the
server with `Ctrl+C`. The preview serves the site **under `/AiSafetyWeb/`**,
exactly like GitHub Pages, so a link that forgets the base path breaks here too
(section 8). `http://localhost:8000/` just redirects there.

### 6.1 What one build does

1. **Delete `_site/` and create it again**, so pages I remove never linger.
2. **Copy `static/`** (CSS and JavaScript) to `_site/static/`.
3. **Render each page** from a Jinja2 template:

   | Output | Template | What it shows |
   |---|---|---|
   | `index.html` | `index.html` | *Today in AI Safety*: entries published in the last 48 h (`home.window_hours`), one group per source, plus a collapsible "New papers on arXiv" block. If nothing is that recent, the 10 latest items |
   | `news/index.html` | `news_index.html` | The archive: one line per month with its item count |
   | `news/YYYY-MM/index.html` | `news_month.html` | All items of a month, grouped by day, with source/topic filters and links to the previous/next month |
   | `papers/index.html` | `papers.html` | Papers: every published entry of `papers.yaml` (newest first) with synopsis, labels, filters and *To read / Read* buttons |
   | `library/index.html` | `library.html` | The Library: one shelf of covers per shelf in `books.yaml`, plus the book cards for the `<dialog>` |
   | `library/<id>/index.html` | `book.html` | One page per book with its full card: what visitors without JavaScript get, and a link that can be shared |
   | `start-here/index.html` | `start_here.html` | Start Here: the stages in order, each reading numbered with its "Why here" note, synopsis (collapsible) and *To read / Read* buttons. While no stage has entries, a short "being put together" message |
   | `my-path/index.html` | `my_path.html` | My Own Path: Timeline, Bookshelf and Journal (section 6.7) |
   | `my-shelf/index.html` | `my_shelf.html` | My shelf: the visitor's marked books (as a shelf) and papers (as a list), and export/import |
   | `about/index.html` | `about.html` | What the site is, the source list (from `sources.yaml`), the result of the last fetch (from `status.json`), the Literata credit and "Built with the help of Claude Code." |
   | `404.html` | `404.html` | "Page not found". GitHub Pages shows it for any unknown address |

   Before rendering, `papers.yaml` and `books.yaml` are **validated** and the publishing rule is
   applied (section 3.1). Skipped entries are listed as `warning: ... not
   published (...)`; broken data stops the build with `BUILD FAILED`.
4. **Check every internal link** (section 8). If one is broken, the build stops
   with `BUILD FAILED` and a list of the bad links, so a broken site never gets
   published.
5. **Check that the local "Add entry" form isn't in the output** (section 6.9).
   If any file in `_site/` contains its markers, the build stops.

The 48 hours are counted back from the **last fetch run** (`last_run` in
`status.json`), not from the moment I build. If I rebuild days later without
fetching, the home page still shows the latest batch instead of going empty.

### 6.2 How the templates fit together

- `base.html` is the page frame: `<head>`, header with the menu, footer with
  the time of the last fetch. Every other template starts with
  `{% extends "base.html" %}` and fills in `{% block content %}`.
- `_macros.html` holds reusable pieces: `entry()` draws one news item (title
  linking to the original, source, date, topic tags, excerpt) and `filters()`
  draws the source/topic menus. Templates use them with
  `{% import "_macros.html" as m %}` … `{{ m.entry(e) }}`.
- `_macros.html` also has `filter_select()` (one filter menu), `paper()` (one
  entry on the Papers page), `authors()` ("A, B and C") and `track_buttons()`
  (the *To read / Read* buttons of one entry, keyed by its `id`). For books:
  `book_cover()` (image over the typographic cover), `book_tile()` (one book on
  a shelf, a link to its page) and `book_card()` (the full card, used by the
  book page and the dialog). `_book_dialog.html` is the one `<dialog>` element.
- The menu comes from `nav:` in `config/site.yaml`: News · Papers · Library ·
  Start Here · My Own Path · About.
  **The site title is the link to the home page (Today)**, so the home page
  needs no menu item, and **My shelf** is a small separate link in the header,
  because it's the visitor's own page, not a section of the site. The current
  page is marked with `aria-current="page"` (screen readers announce it, and
  the CSS makes it bold).

### 6.3 Safety measures in the generator

- **Autoescaping:** every value inserted into the HTML is escaped, so a feed
  title like `<script>…</script>` is shown as text and never runs.
- **Only http(s) links from feeds** (`safe_url` filter): a malicious feed
  could send a `javascript:` link; it becomes `#` instead.
- **`StrictUndefined`:** a typo in a template (`{{ entyr.title }}`) stops the
  build with an error instead of silently printing nothing.
- External links carry `rel="noopener"`, so the opened page can't control mine.

### 6.4 JavaScript: filters (progressive enhancement)

The HTML already contains every item, so every page works **without
JavaScript**. `static/js/filters.js` only adds the filter menus (source/topic
on the news month pages; year/type/topic/difficulty on Papers): the menus
start `hidden` and the script shows them, then hides the items that don't
match. It is generic: a menu `<select data-filter="type">` keeps an item if the
chosen value is one of the words in the item's `data-type` attribute (topics
are several words: `data-topics="alignment evals"`). Days with no visible
items are hidden too, and a counter says "12 of 134 shown". The CSS rule
`[hidden] { display: none !important; }` makes sure the `hidden` attribute
always wins.

### 6.5 JavaScript: the reading tracker and My shelf

Small scripts, loaded only on the pages that need them (Papers, the Library,
book pages and My shelf), in this order:

1. **`reading-store.js` — the `ReadingStore`.** All reading marks go through
   one small interface: `get(id)`, `set(id, status)` (`"to-read"`, `"read"`
   or `null` to remove), `all()`, `merge(items)` (for imports),
   `subscribe(fn)` and `persistent`. Today it's implemented with
   **localStorage** (section 3.1 has the stored format). Every access is
   wrapped in `try/catch`: localStorage can be missing or blocked (private
   windows, strict privacy settings, full storage). Then the store keeps marks
   in memory for that page only and My shelf shows a warning. A corrupt stored
   value is ignored instead of breaking the page. If another tab changes the
   marks, the `storage` event keeps every open tab in sync.

   **Why an interface:** pages never touch localStorage directly. If one day
   there are accounts and marks live on a server (section 12), I only write a
   second store with the same methods; the pages don't change.
2. **`tracker.js` — the buttons.** Every entry has *To read* and *Read* buttons
   in the HTML, but hidden: without JavaScript there is nowhere to save a
   mark. The script shows them and sets `aria-pressed="true"` on the saved
   status (screen readers announce "pressed", and the CSS fills the button).
   Clicking the active button again removes the mark. One click listener for
   the whole page handles every button, so buttons that `my-shelf.js` moves
   around keep working.
3. **`library.js` — the Library** (also on book pages and My shelf).
   - **Cover fallback:** if a cover image fails to load, it's removed and the
     typographic cover underneath shows. (Without JavaScript the image has an
     empty `alt`, so a broken one shows nothing and the typographic cover still
     shows.)
   - **Marks on the shelf:** each book shows a small *To read* / *Read* badge.
   - **The book card `<dialog>`:** every book on a shelf is a normal link to
     its page. With JavaScript, a plain click copies that book's card from a
     `<template data-card="<id>">` (rendered by the build, not part of the page
     until copied) into the one `<dialog>` and opens it with `showModal()`.
     The browser moves focus into it and makes the rest of the page inert;
     `Esc`, the × button (a `method="dialog"` form) or a click on the dark
     backdrop close it, and focus returns to the book that opened it. The
     dialog is labelled by the book's title for screen readers.
     Ctrl/Cmd-click still opens the book page in a new tab. A detail I had to
     fix: the browser fires the `close` event a moment *after* closing, so the
     handler doesn't empty the dialog if a book was reopened in between.
4. **`my-shelf.js` — My shelf.** The page contains a hidden catalogue of every
   published book and paper. The script **moves** the marked ones into the
   *To read* and *Read* sections (books as a shelf of covers that open the
   same dialog, papers as a list; moving, not copying, so no element exists
   twice) and back when a mark is removed. Marks for entries that aren't on the site right now
   (removed, or not published yet) are kept and exported, and a note says how
   many there are.
   - **Export** builds the JSON file in the browser (a `Blob`) and downloads it
     as `ai-safety-web-shelf-YYYY-MM-DD.json`. Nothing is uploaded anywhere.
   - **Import** reads a file chosen by the visitor (max 1 MB), checks that it
     is valid JSON with `"format": "aisafetyweb-reading"`, keeps only valid
     marks (an `id` that is a slug, a status of `to-read` or `read`) and
     **merges** them into the shelf: new ones are added, and where both have a
     mark for the same entry, the imported one wins. A message reports
     "Imported N marks: X new, Y changed, Z invalid ones skipped".

The page says clearly that marks are **stored only in this browser**, and
without JavaScript it explains why the shelf can't be shown.

### 6.6 Start Here: how the path is built

`build_site.py` takes the stages from `start_here_stages` (in order) and puts
into each one the published papers whose `start_here.stage` points to it,
sorted by `start_here.order`. A paper whose `start_here` block has no `note`
(or a `TODO` in it) stays out of the path but remains in Papers. Two papers
with the same `order` in one stage stop the build. Stages without any entry
are not shown. The *To read / Read* buttons use the same `id` as in Papers, so
a mark set in Start Here shows up in Papers and My shelf too.

### 6.7 My Own Path: timeline, bookshelf and journal

All of it is built in Python; the page works without JavaScript. The order on
the page is Timeline → Bookshelf → Journal.

- **Timeline:** newest first, as a vertical line with one dot per stage
  (filled when completed). Each stage is a `<details>` element: the summary
  shows dates, title, type, status and the number of days; clicking opens
  provider, link, my notes and how many readings point to it with `via` (a
  link to that month in the Journal). The **duration bar** is the stage's
  length relative to the longest stage; an in-progress stage counts until the
  day of the build and its bar is lighter. Each stage has the anchor
  `#timeline-<id>`.
- **Bookshelf:** "Reading now" and "Finished" shelves with the same covers as
  the Library. A book with `book_ref` is the Library's own tile and opens the
  same card (with my `my_opinion`) in the `<dialog>`; a book that's not in the
  Library links to its own `url`, with its `cover_id` cover or a typographic one.
- **Journal** (it replaced the Reading log in Stage 7): everything I did, one
  month at a time. `build_journal()` in `build_site.py` puts into each month:
  - the readings and resources of that month (`month` in `reading_log.yaml`);
  - the Timeline stages that **started**, were **in progress** or were
    **completed** in it (a stage still in progress runs until the current
    month; a milestone belongs to its own month only);
  - the books I **started** (`started`), was still **reading**, or
    **finished** (`month`). A book I'm reading without a `started` month has
    no month to show in: it's only on the Bookshelf.

  Each month shows a summary line ("2 courses · 3 essays · 6 articles…") and
  the entries **grouped by type** (courses, projects, milestones, books, then
  the reading types), each group with its counter. Every entry shows its
  state where it has one ("Started", "In progress", "Completed", "Reading",
  "Finished").
- **Activity-per-month chart:** a plain HTML list, one bar per month from the
  first to the last (empty months included, as a zero), the number written
  next to each bar, one colour, so it reads without colours, without
  JavaScript and with a screen reader. A bar counts the readings of that month
  (a book counts in the month I finished it) **plus** the Timeline stages that
  started or ended in it, each stage once per month. A stage that is simply
  still in progress doesn't add to the bar, or a long course would inflate
  every month. Each bar with entries is a link to its month
  (`#journal-2026-09`).
- **Month selector (`static/js/journal.js`):** one drop-down with every month
  that has entries (newest first) and *Older* / *Newer* buttons. The chosen
  month goes into the URL (`#journal-2026-09`), so it can be linked, and the
  browser's Back button works. Without a month in the URL it shows the newest
  month with activity. Clicking a bar of the chart just follows its link, and
  the script shows that month.
- **Without JavaScript** there is no selector: every month is shown, newest
  first, and the chart's bars are links that jump to each month.
- **Ready for more people (not used yet):** the Journal carries the owner's id
  (`data-person="marco"`, from `my_path.person` in `config/site.yaml`) on the
  section and on every month. Section 12 explains how a person selector would
  build on it.

### 6.8 Styles: the e-reader design

I wanted the site to read like a book on an e-reader, so the design is
deliberately quiet. Everything is in `static/css/style.css`.

- **One typeface: Literata**, a serif made for reading on screens (by
  TypeTogether, first for Google Play Books). I serve it **from the site
  itself** (`static/fonts/`, two variable `.woff2` files of ~50 KB each, Latin
  subset), not from Google Fonts, so visitors' browsers never contact a third
  party. It's under the SIL Open Font License 1.1, which allows this; the
  licence travels with the files (`static/fonts/Literata-OFL.txt`) and About
  credits it. `base.html` preloads the regular file so text appears in the
  right face quickly; `font-display: swap` shows Georgia until it arrives.
- **Ink on paper, no colour.** Sepia paper in light mode, near-black in dark
  mode. Links are the text colour, told apart by their underline; pressed
  *To read / Read* buttons are filled with ink. The only colours are the book
  covers (and the cloth colours of the typographic covers).
- **Book layout.** A 620px column; the header centred like a running head,
  with the menu in italics; every page title opens like a chapter, with a ⁂
  underneath; Start Here stages open like chapters too, separated by a ❦.
  Labels and topics are small caps; secondary data (authors, dates) is italic.
- **Drop cap only where there's an introduction:** the `drop-cap` class is set
  in the templates of Start Here, My Own Path, the Library and About (on the
  first long paragraph there; the tagline is only one line). Today, News,
  Papers and My shelf keep the chapter title but no drop cap: they are lists,
  and they should be quick to scan.
- **Justified text with hyphenation.** Paragraphs of prose (introductions,
  synopses, About) are justified with `hyphens: auto`, which works because the
  page says `lang="en"`; only words of 7+ letters are split. List excerpts, the
  book card (its column is narrow) and everything on phones (≤ 34rem) stay
  ragged-right without hyphenation, because narrow justified lines open big
  gaps and many hyphens make lists hard to scan.
- **Keyboard focus.** With no link colour, focus has to be unmistakable:
  everything focusable gets a 3px ink ring with a paper-coloured gap
  (`:focus-visible`), links also get a light background, and a book on the
  shelf gets the ring around cover and caption.

**Colour tokens and contrast.** Every colour is a CSS variable on `:root`
(`--bg`, `--surface`, `--text`, `--muted`, `--line`), redefined for dark
mode. WCAG AA asks for 4.5:1 for normal text and 3:1 for large text; I checked
every pair that carries text:

| Pair | Light | Dark |
|---|---|---|
| Text (`--text`) on paper (`--bg`); also links, unpressed buttons | 13.95 | 12.90 |
| Secondary text, labels, dates (`--muted`) on paper | 6.16 | 6.34 |
| Text on notices (`--surface`) | 12.62 | 11.63 |
| Secondary text on notices | 5.58 | 5.71 |
| Pressed button: paper colour on ink | 13.95 | 12.90 |
| Typographic cover text (`#fbf8f1`) on the six cloth colours | 6.95–9.22 | same |

`--line` (the rules between entries) is decorative, not text, so it's allowed
to be faint. The focus ring is ink on paper (≥ 12.9:1).

**Light and dark.** Without JavaScript, or until the visitor chooses, the site
follows the system setting (`prefers-color-scheme`). The *Dark mode / Light
mode* link in the header (`static/js/theme.js`, hidden without JavaScript)
sets `data-theme` on `<html>` and saves the choice in localStorage under
`theme`. A two-line inline script at the top of `base.html` applies a saved
choice **before** the page is painted, so there's no flash of the wrong theme.
The CSS has the dark values twice: once inside the media query (for "system
is dark and the visitor didn't choose light") and once for
`[data-theme="dark"]`.

**How I checked it.** Every page (Today, News and a month page, Papers, the
Library with a book card open, Start Here, My Own Path, My shelf with test
marks, About, 404) in light and dark, at desktop width and at 360px, in
headless Edge: no horizontal scrolling anywhere. Plus keyboard focus on a
link, a button (pressed and not), a filter and a book, in both themes, and
the toggle (starting from a light and from a dark system, remembered after a
reload).

### 6.9 The local "Add entry" form (my computer only)

To add things to My Own Path without editing YAML by hand, the preview server
(`python scripts\build_site.py --serve`) has a small form. It exists **only**
in that preview on my computer: it is never part of the published site or of
the GitHub Actions build.

**How it stays off the published site.**
- The form page is generated **in memory** by the preview server
  (`scripts/local_form.py`, template `templates/local/add_entry.html`) at
  `/AiSafetyWeb/_local/add-entry/`. It is never written to `_site/`.
- The "Add entry" link on My Own Path is also added in memory, while the
  preview server sends that page. The file in `_site/my-path/` doesn't have it.
- The form's CSS and JavaScript are inside its own page, not in `static/`,
  because everything in `static/` is published.
- **A safety net in the build:** `check_no_local_tools()` fails the build if
  any file in `_site/` contains the form's markers (`data-local-only` or
  `/_local/`). If I ever put a piece of the form in a published template by
  mistake, the build (locally and in Actions) stops with
  `BUILD FAILED: local-only form code found in the output`.

**What it does when I save.**
1. It turns the form into an entry and validates it with the **same
   functions the build uses** (`check_timeline_item` / `check_log_entry`):
   types, date and month formats, URLs without `utm_`, `via` and
   `paper_ref` / `book_ref` pointing to existing entries, a unique id, a
   finished book with its month… Every problem is shown next to its field,
   and nothing is saved while there is one. With a `paper_ref` / `book_ref`
   it also asks me to leave title, author, source and URL empty (they come
   from Papers / the Library).
2. It **inserts text** into the YAML file instead of loading and re-saving it
   (re-saving with PyYAML would delete my comments):
   - Timeline → appended at the end of `timeline.yaml` (the site sorts by date).
   - Journal → inserted right under `entries:` in `reading_log.yaml`, the
     newest at the top, like the rest of the file.
   Titles, authors, sources and months are written in double quotes, dates
   bare (so YAML reads them as dates), notes as a folded `>` block.
3. It writes the new version to a temporary file, **validates the whole
   file** with the build's loaders and only then replaces the real one. If
   anything is wrong, the real file is untouched.
4. It rebuilds the preview and shows which file changed and the block it
   added. **It never commits or pushes**: I check the change with `git diff`
   and commit it myself.

**Protections.** The form writes files on my computer, so only I must be able
to use it:
- **Only my computer:** the preview server listens on `127.0.0.1`, not on the
  network, so other devices can't even connect.
- **Host check (against DNS rebinding):** every request to the form must say
  `Host: 127.0.0.1:<port>` or `Host: localhost:<port>`. In a DNS rebinding
  attack, a malicious website makes its own domain point to `127.0.0.1` so my
  browser talks to my local server; the browser still sends the attacker's
  domain as `Host`, so the request is refused (403).
- **Origin check:** a save must come from a page of this preview (`Origin:
  http://127.0.0.1:<port>` or `http://localhost:<port>`; if the browser sends
  no `Origin`, the `Referer` must match). Another website open in my browser
  can't post to the form.
- **A secret token:** the server makes a new random token each time it starts
  and puts it in the form; a save without the current token is refused. (After
  restarting the server I reload the form.)
- **Small requests only** (64 KB), `Cache-Control: no-store`, and the page
  can't be shown inside a frame of another site.

## 7. GitHub Actions and the cron schedule

Everything automatic happens in **one workflow**,
`.github/workflows/update-and-deploy.yml`. GitHub runs it on its own servers
(a fresh Ubuntu machine each time), so my computers can be off.

### 7.1 When it runs, and what each trigger does

| Trigger | When | What it does |
|---|---|---|
| `schedule` | every day at **06:00 UTC** (`cron: "0 6 * * *"`) | fetch news → commit data if it changed → build → deploy |
| `workflow_dispatch` | when I press **Run workflow** in the Actions tab (or `gh workflow run`) | the same as the daily run |
| `workflow_dispatch` with `check_feed` filled in | same button, with a feed URL in the field | **only** tests that feed and prints a report (section 9, *Add a news source*); no fetch, commit or deploy |
| `push` to `main` | every time I push | build → deploy only: **no fetching** |

**How the workflow tells a push from the daily run:** GitHub gives every run
the name of the event that started it, `github.event_name` (`schedule`,
`workflow_dispatch` or `push`). The fetch and commit steps have
`if: github.event_name != 'push'`, so on my pushes they are skipped and the
site is rebuilt from exactly what I pushed. That way my own commits deploy
quickly and never mix in new data I haven't seen.

**Why one workflow and not two:** commits made by a workflow with the built-in
`GITHUB_TOKEN` **do not start other workflows** (GitHub does this on purpose,
to avoid endless loops). A separate "deploy on push" workflow would never see
the robot's data commits, so the daily data would never be published. In one
workflow, the same run fetches, commits and deploys.

**Scheduled runs can be late.** GitHub starts `schedule` runs when it has
capacity, so "06:00" often means some minutes later, sometimes much later at
busy times. That's fine for a daily site.

### 7.2 The steps

Job **`build`** (permission: `contents: write`, to push the data commit):
1. **Check out** the repository.
2. **Set up Python** with the version in `.python-version` (3.12, the same as
   on my computers) and **pip's cache** keyed on `requirements.txt`, so the
   packages download only when the requirements change.
3. **Install** `requirements.txt` (pinned versions).
4. *(Only a manual run with `check_feed`)*: `fetch_news.py --check-feed <URL>`
   and stop.
5. *(Not on push)* **Fetch**: `python scripts/fetch_news.py`. If *every*
   source fails it exits with 1, the run fails and GitHub emails me.
6. *(Not on push)* **Commit the data only if it changed**: `git add data/`;
   if `git diff --cached --quiet` says nothing is staged, it stops there.
   Otherwise it commits as **`github-actions[bot]`** ("Update news data
   (automated)"), then **`git pull --rebase origin main`** and
   `git push origin HEAD:main`. The rebase matters when I pushed something
   while the run was fetching: the robot's commit is placed on top of mine
   instead of the push being rejected. (`data/status.json` has the time of
   the run, so in practice there's a data commit every day.)
7. **Build** the site (`python scripts/build_site.py`), with every check of
   the local build: data validation, internal links, no local form.
8. **Upload** `_site/` as the Pages artifact (`upload-pages-artifact`).

Job **`deploy`** (needs `build`; permissions: `pages: write` and
`id-token: write`): **deploys** the artifact with `deploy-pages` to the
`github-pages` environment. `id-token: write` lets the job get a short-lived
signed token (OIDC) that proves to GitHub Pages which workflow run is
deploying; there is no password or long-lived key anywhere.

### 7.3 Safety choices in the workflow

- **Minimal permissions:** the workflow starts with `permissions: {}` (nothing)
  and each job asks only for what it needs: `build` can write repository
  contents (for the data commit), `deploy` can write Pages and request the
  OIDC token. The repository's default for the token is read-only
  (Settings → Actions → General → Workflow permissions).
- **Every action pinned to a full commit SHA**, with the version in a comment:
  ```yaml
  uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  ```
  A tag like `@v7` is just a label its owner can move to different code; a
  commit SHA always means the same code. The repository also has
  **"Require actions to be pinned to a full-length commit SHA"** turned on,
  so GitHub refuses a workflow that uses a tag. Only actions made by GitHub
  (`actions/…`) are allowed, and they are the only ones I use:
  `checkout` v7.0.1, `setup-python` v7.0.0, `upload-pages-artifact` v5.0.0
  (which itself uses `upload-artifact` pinned by SHA) and `deploy-pages`
  v5.0.1.
- **The `check_feed` URL is never pasted into the script.** It goes in an
  environment variable (`FEED_URL`) and the script reads `"$FEED_URL"`, so a
  URL with shell characters can't run commands.
- **`concurrency`** (group `update-and-deploy`, `cancel-in-progress: false`):
  never two runs at once. If I push during the daily run, my run waits for it
  to finish instead of both pushing or deploying at the same time, and nothing
  is cancelled halfway through a commit or a deployment.
- **Time limits:** 20 minutes for `build`, 10 for `deploy`, so a hung
  download can't run for hours.

**Updating a pinned action (e.g. once or twice a year):** I look up the new
release on the action's GitHub page (Releases), take the **full commit SHA**
of that release's tag, and replace both the SHA and the version comment. To
get the SHA from the terminal:
`gh api repos/actions/checkout/commits/v7.0.1 --jq .sha`. Then I push and
check that the run is green.

### 7.4 Monitoring: how I find out something is wrong

- **A failed run → an email.** In my GitHub account settings
  (Settings → Notifications → Actions) I have email notifications for
  **failed workflows only**. A run fails when all sources fail, when the data
  push can't be rebased, when the build finds a problem, or when the
  deployment fails.
- **A site that stopped updating → a warning on the site.** Every page has a
  hidden notice, *"This site may be out of date"*, with the time of the last
  fetch (`last_run` from `data/status.json`). `static/js/stale.js` shows it
  when that time is more than `stale_after_hours` (48, in `config/site.yaml`)
  in the past **by the visitor's clock**. The check has to run in the
  browser: if Actions stops, nothing rebuilds the site, so a check made at
  build time would never fire. Without JavaScript the notice stays hidden,
  and the footer still shows "News last fetched …".
- **The Actions tab** (https://github.com/Marcobm1/AiSafetyWeb/actions) lists
  every run with its logs; `gh run list --workflow update-and-deploy.yml`
  shows the same in the terminal.
- **The 60-day rule.** GitHub disables *scheduled* workflows in a public
  repository when there has been no repository activity for 60 days. The
  daily data commit should count as activity, but if GitHub ever disables the
  workflow it usually sends me an email first, and the site's warning appears
  48 hours after the last fetch. How to switch it back on is in section 11.

### 7.5 Repository settings this depends on

- **Settings → Pages → Build and deployment → Source: "GitHub Actions"**
  (not "Deploy from a branch").
- **Settings → Actions → General:** "Allow Marcobm1, and select non-Marcobm1,
  actions and reusable workflows" with **"Allow actions created by GitHub"**;
  **"Require actions to be pinned to a full-length commit SHA"** on; Workflow
  permissions **"Read repository contents and packages permissions"**; "Allow
  GitHub Actions to create and approve pull requests" **off**.
- **Settings → Environments → `github-pages`:** created by GitHub for Pages;
  only `main` may deploy to it.

## 8. Deployment to GitHub Pages and the base path

The site is deployed by the workflow's `deploy` job (section 7.2): the build
uploads `_site/` as an **artifact** (a packed copy of the folder) and
`deploy-pages` publishes it. Nothing is committed to a `gh-pages` branch, and
`_site/` is never in the repository. Each deployment replaces the whole site,
so a page I delete disappears online too.

Published address: **https://marcobm1.github.io/AiSafetyWeb/**. The Actions
tab shows each deployment with a link to the site, and Settings → Pages shows
the current one.

**What is never published:** the local "Add entry" form and anything under
`_local/`. The workflow runs `build_site.py` without `--serve`, so the form
never exists there, and the build's `check_no_local_tools()` would fail the
run if any of its markers reached `_site/` (section 6.9).

**The base path problem:** this is a *project site*, so it lives under a
sub-folder: `https://marcobm1.github.io/AiSafetyWeb/`. A link written as
`/css/style.css` would point to `https://marcobm1.github.io/css/style.css`,
which does not exist. Every internal link and asset must be prefixed with
`/AiSafetyWeb/`.

**How I handle it:**
1. The prefix is defined **once**, as `base_path` in `config/site.yaml`.
2. Templates **never** write internal links by hand. They call the `url()`
   helper: `{{ url('news/') }}` → `/AiSafetyWeb/news/`,
   `{{ url('static/css/style.css') }}` → `/AiSafetyWeb/static/css/style.css`.
3. After every build, `build_site.py` scans all generated HTML: every `href`
   or `src` that starts with `/` must start with `/AiSafetyWeb/` **and** point
   to a file that exists in `_site/` (a link ending in `/` means that folder's
   `index.html`). Otherwise the build fails and lists the bad links.
4. The local preview also serves the site under `/AiSafetyWeb/`, so I see the
   same result as on GitHub Pages.

If the repository were ever renamed, I'd only change `base_path` and `site_url`
in `config/site.yaml`.

`_site/` also gets an empty `.nojekyll` file. It tells GitHub Pages to publish
the files as they are instead of running its own site generator (Jekyll) on them.

## 9. How to…

- **Add a news source:**
  1. Find the site's real feed URL. I look in the page's HTML for
     `<link rel="alternate" type="application/rss+xml" href="...">`, or try the
     usual paths (`/feed`, `/rss.xml`, `/feed.xml`; Substack blogs always use
     `/feed`). **I never add a URL I haven't opened.**
  2. Add a block under `sources:` in `config/sources.yaml` with a new `id`, the
     `name` to show on the site and the `url`. If the source also publishes
     off-topic posts, add `require_topic: true`.
  3. Test the feed on its own first:
     `python scripts\fetch_news.py --check-feed <URL>`. It fetches that URL
     the way the daily run would (same User-Agent, same age and topic
     filters), prints how many items it has, how many recent ones match a
     topic and the newest five, and **writes nothing**. If the feed fails from
     my network (like DeepMind's from my work computer), I test it from GitHub
     instead: Actions → *Update and deploy* → **Run workflow**, paste the URL
     in *check_feed*, run, and read the "Check one feed" step. That run only
     tests the feed (no fetch, commit or deploy). From the terminal:
     `gh workflow run update-and-deploy.yml -f check_feed=<URL>`.
  4. Run `python scripts\fetch_news.py --dry-run` and check the new source's
     line says `ok` and keeps a sensible number of items.
  5. Run it for real (or let the daily bot do it), update the source table in
     section 5.3, and commit.
- **Remove or pause a source:** delete its block in `config/sources.yaml` (its
  old entries stay in `data/news/`, which is fine), and update section 5.3.
- **Change the topic keywords or the arXiv phrases:** edit `topics:` or
  `arxiv.phrases` in `config/sources.yaml`, then check with `--dry-run`. New
  keywords only apply to entries fetched from then on; existing entries keep
  their topics.
- **Check whether the last run went well:** open `data/status.json` (on GitHub
  or locally) and look for `"status": "error"`.
- **Add a paper (or essay, report, scenario, post) by hand:**
  1. Open the original and **verify** the exact title, all authors (or the
     first three + `"et al."`), the year, the type and the URL. I remove any
     `utm_…` parameters. For arXiv papers I also note the arXiv number.
  2. Pick an `id`: a short lowercase slug (`sleeper-agents`) that isn't used in
     `papers.yaml` or `books.yaml`. It never changes once published.
  3. Add a block at the end of `data/papers.yaml` (template at the top of the
     file; `entries` stays the last key), with `tags` from the five topics and
     a `difficulty`.
  4. Write the `synopsis`: 2–4 neutral sentences in my own words, based on the
     text itself (not the abstract, publisher text or reviews). Add
     `why_it_matters` and `my_opinion` if I want; both are optional.
  5. Run `python scripts\build_site.py`: it validates the entry (section 3.1)
     and says if something is wrong. Then commit and push.
- **Promote a paper candidate to Papers:**
  1. I look through `data/paper_candidates.json` (on GitHub or in VS Code) and
     copy the `id` of a paper I like, e.g. `arxiv:2401.05566`.
  2. I run `python scripts\promote_candidate.py arxiv:2401.05566` (add
     `--id sleeper-agents` to choose the `id`, `--type report` for another
     type, `--dry-run` to only see the block). It appends a ready-made block to
     the end of `papers.yaml` with the title, authors (first three +
     "et al."), year, URL, arXiv id and topics filled in, and `synopsis` and
     `difficulty` set to `TODO` (and `tags` too if the candidate had no
     topics). It appends plain text instead of rewriting the whole file, so my
     comments in `papers.yaml` survive; it checks that the result is still
     valid YAML with `entries` last before saving. It refuses candidates that
     are already in `papers.yaml`, unknown candidate ids and `id`s already used.
  3. I open `papers.yaml`, check the generated `id`, and replace the `TODO`s
     with the synopsis and the difficulty (and topics).
  4. `python scripts\build_site.py`: while a `TODO` is left, it prints
     `warning: ... not published` and skips the entry. Then commit and push.
     On the next run the fetch script sees the paper in `papers.yaml` and
     drops it from the candidates.
- **Add a book to the Library (with its cover):**
  1. On the **publisher's or author's page**, check the most recent English
     edition: exact title and subtitle, authors, edition number, publisher and
     year.
  2. On **openlibrary.org**, search the book, open *that* edition (the ISBN on
     the page should match the publisher's) and copy:
     - the **edition OLID**: the `OL…M` in the address
       (`openlibrary.org/books/OL27724147M/...`);
     - the **cover id**: right-click the cover → *Copy image address*; it's the
       number in `covers.openlibrary.org/b/id/<number>-L.jpg`.
     I open `https://covers.openlibrary.org/b/id/<number>-M.jpg` to check it's
     the right cover and edition. If Open Library has no cover, I leave
     `cover_id` out: the site draws a typographic cover.
  3. Add a block to `data/books.yaml` (template at the top of the file) with a
     `shelf` from `shelves` and an `id` not used in `papers.yaml` or
     `books.yaml`. `url` is `https://openlibrary.org/books/<OLID>`. Add
     `free_url` only if the authors or the publisher offer the full book for
     free themselves.
  4. Write the `synopsis` (2–4 neutral sentences in my own words, never the
     publisher's blurb), optionally `why_it_matters` and `my_opinion`.
  5. `python scripts\build_site.py`: it validates the block and creates the
     book's page `library/<id>/`. Preview, then commit and push.
- **Add a new shelf:** add `{id, title}` under `shelves:` in `books.yaml` (the
  order there is the order on the page) and use its `id` as the `shelf` of its
  books. Typographic covers take their colour from the shelf's position; there
  are colours for six shelves in `style.css` (`.cover-shelf-0` … `-5`), so a
  seventh needs one more rule.
- **Test the Library locally:**
  1. `python scripts\build_site.py --serve` and open
     http://localhost:8000/AiSafetyWeb/library/.
  2. Six shelves with 20 books; *AI Snake Oil*, *Understanding Deep Learning*,
     *Introduction to Probability* and *Automate the Boring Stuff* have
     typographic covers (no cover on Open Library).
  3. Click a book: its card opens over the page. Try `Esc`, the × and a click
     outside the card; each closes it and the focus goes back to the book.
     Try it with the keyboard only: `Tab` to a book, `Enter` opens, `Esc`
     closes.
  4. In the card, click *Read*: after closing, the book shows a *Read* badge.
     *Deep Learning* shows "Free version (official)"; *Superintelligence* doesn't.
  5. Open **My shelf**: the book appears as a cover under *Read → Books*; click
     it to open the same card and change its status.
  6. Without JavaScript: clicking a book opens its own page
     (`library/<id>/`) with the same card, without buttons.
- **Test the reading tracker and My shelf locally:**
  1. `python scripts\build_site.py --serve` and open
     http://localhost:8000/AiSafetyWeb/papers/.
  2. Click *To read* on one entry and *Read* on another: the button fills in.
     Click it again: the mark is removed. Reload: the marks are still there.
  3. Open **My shelf** (top right): both entries are in their lists. Change one
     with its buttons: it moves to the other list.
  4. **Export**: a file `ai-safety-web-shelf-<date>.json` is downloaded. Open
     it in VS Code to see the format.
  5. Clear the marks (click the active buttons, or DevTools `F12` →
     Application → Local storage → delete `aisafetyweb.reading.v1`), reload,
     then **Import…** the file: the message says how many marks came back.
     Importing a random `.json` shows "not a shelf export" and changes nothing.
  6. Private window: the buttons work, and My shelf may show the warning that
     marks will be lost when the window closes (it depends on the browser).
  7. Without JavaScript (DevTools → `Ctrl+Shift+P` → "Disable JavaScript"):
     Papers shows every entry without buttons or filters; My shelf explains it
     needs JavaScript.
- **(Optional, later) Add a hidden page to review candidates:** I decided to
  keep candidates **only in the repo**: new arXiv papers already appear on the
  home page and in the news archive, so a public "Recent papers" page would
  duplicate them and mix unreviewed papers with my curated Library. If reading
  the JSON ever becomes tedious, this is how I'd add a private-ish review page:
  1. Create `templates/candidates.html` that lists the candidates (title,
     authors, date detected, topics, link, and the `id` to copy for
     `promote_candidate.py`).
  2. In `build_site.py`, load `data/paper_candidates.json` and render that
     template to `_site/review/candidates/index.html`.
  3. Add `<meta name="robots" content="noindex, nofollow">` to its `<head>`
     so search engines don't list it, and **don't link it from the menu**.
  4. Remember that it is still **public**: anyone with the URL can open it.
     "Hidden" only means unlinked and unindexed, not protected.
- **Add an entry to the Start Here path:**
  1. The reading must be a published entry of `papers.yaml`, verified against
     the original source.
  2. If its stage doesn't exist yet, add `{id, title, intro}` to
     `start_here_stages` (order in the list = order on the page).
  3. Add to the entry:
     ```yaml
         start_here:
           stage: why-it-matters   # an id from start_here_stages
           order: 2                # position inside the stage (whole number, unique there)
           note: >
             Why it sits at this point of the path.
     ```
  4. Build and check `/start-here/`; then commit and push.
- **Add an entry to My Own Path with the form (the easy way):**
  1. `python scripts\build_site.py --serve`, open
     http://localhost:8000/AiSafetyWeb/my-path/ and click **Add entry** (just
     under the introduction; the terminal also prints the form's address).
  2. In **What to add**, choose the type: *Timeline · Course / Project /
     Milestone* or *Journal · Paper / Report / Essay / Article / Book /
     Resource / Podcast / video*. Only the fields of that type are shown.
  3. Fill it in. The same checks as in the manual steps below apply: I verify
     title, author and URL against the original first, remove `utm_…`, use a
     Wayback Machine copy for `archive_url`, and pick `via`, *Already in
     Papers?* or *Already in the Library?* from the lists instead of typing ids.
     Timeline: dates by day (the date picker), `Id` is suggested from the
     title. Journal: the month (for a book, the month I finished it; for a
     book I'm still reading: status *Reading*, no month, optional *Started*).
  4. **Save entry.** If something is wrong, the page lists the problems and
     marks each field; my values stay in the form. Fix and save again.
  5. When it's saved, the page shows the file that changed and the exact
     block added, and a link to see it on My Own Path (the preview is
     already rebuilt).
  6. In the terminal: `git diff data/my_path/` to review, then commit and push
     as usual. The form never commits.
- **Add a reading to My Own Path by hand:**
  1. Open the original and **verify** the exact title, the author(s), the
     publication and the URL. I remove any `utm_…` parameters from the URL.
  2. If it's a paywalled article, I look for an archived copy on the Wayback
     Machine (`web.archive.org`), check that it opens and shows the right
     headline and author, and keep its URL for `archive_url`. I don't use
     archive.ph / archive.today: it is blocked in Spain, so visitors from here
     would only see a block page.
  3. If the text is already in Papers (`data/papers.yaml`) or the Library
     (`data/books.yaml`), I only need its `id` for `paper_ref` / `book_ref` and
     can skip title, author, source and URL. My opinion of it then goes in its
     `my_opinion` there, not in `notes`.
     For a **book**, I add `status: reading` when I start it (optionally
     `started: "YYYY-MM"`), and when I finish it I change it to
     `status: finished` and add `month:` with the month I finished.
  4. Open `data/my_path/reading_log.yaml` and add a block under `entries:`,
     indented like the template at the top of the file:
     ```yaml
       - month: "2026-09"
         type: article
         title: "Exact title"
         author: "Author Name"
         source: "Publication"
         url: https://...
         via: agi-strategy        # only if I read it as part of a Timeline stage
         notes: >
           What I took from it.
     ```
     `type` is one of paper, report, essay, article, book, resource,
     podcast-video. `via` is the `id` of a stage in `timeline.yaml`.
     For a book that is not in the Library I can add `cover_id` (found as in
     *Add a book to the Library*) for its cover on my Bookshelf.
  5. Run `python scripts\build_site.py` to check nothing is broken (it
     explains any mistake), then commit and push. The site updates on the next
     deploy.
- **Add a stage to the My Own Path Timeline by hand:** (or use the form above)
  add a block to `data/my_path/timeline.yaml` with a new `id` (short slug that I never change),
  `type` (course, project or milestone), `date`, `title`, `status` and, when
  I have them, `provider`, `url` and `notes`. When I finish it, I add
  `completed: YYYY-MM-DD` and change `status` to `completed`. Notes that still
  say `TODO` are not shown on the site.
- **Test Start Here and My Own Path locally:**
  1. `python scripts\build_site.py --serve`, open
     http://localhost:8000/AiSafetyWeb/my-path/.
  2. The order is Timeline, Bookshelf, Journal. Timeline: two stages, newest
     first, with duration bars; click one to open it (AGI Strategy says "14
     readings in the Journal").
  3. Bookshelf: empty for now, with a short message.
  4. Journal: the chart shows *Sep 2026* with 16 (14 readings + Future of AI
     and AGI Strategy, which started or ended in September). The selector
     shows *September 2026* (Older / Newer disabled: it's the only month), with
     "2 courses · 2 reports · 3 essays · 6 articles · 3 resources" and the
     entries grouped by type. "via AGI Strategy" jumps to the timeline; the
     Vox article has "archived copy". The URL gets `#journal-2026-09` when I
     pick the month.
  5. Without JavaScript (DevTools → Ctrl+Shift+P → "Disable JavaScript", then
     reload): no selector; every month is shown, newest first; the chart's
     bars are links to each month. The "Add entry" link is still there
     (it's added by the preview server, not by JavaScript).
  6. http://localhost:8000/AiSafetyWeb/start-here/ shows 4 stages (Why it
     matters, The alignment problem, Evidence from today's models, What
     researchers are doing about it) with 3, 4, 2 and 3 readings; a *Read*
     mark there also shows in Papers.
  7. The menu shows News · Papers · Library · Start Here · My Own Path · About.
- **Preview the site after any change:** `python scripts\build_site.py --serve`
  and open http://localhost:8000/AiSafetyWeb/ (section 6).
- **Change the menu:** edit `nav:` in `config/site.yaml` (`label` shown,
  `path` relative to the base path, e.g. `news/`).
- **Change how many hours the home page covers:** `home.window_hours` in
  `config/site.yaml`.
- **Change a topic's label on the site:** `topics:` in `config/site.yaml`
  (the topic ids themselves live in `config/sources.yaml`).
- **Add a new page:** create a template that starts with
  `{% extends "base.html" %}`, add a `render(...)` call for it in `build()` in
  `scripts/build_site.py`, use `url('...')` for every internal link, and add it
  to `nav:` if it belongs in the menu. The link check will tell me if I got a
  path wrong.
- **Change the design:** edit `static/css/style.css` (section 6.8). To change
  a colour, change its token in **both** places (light `:root`, and the dark
  values, which appear twice) and recheck the contrast table in 6.8: at least
  4.5:1 for text. Then preview both themes (the *Dark mode* link) at desktop
  and phone width (DevTools → device toolbar, 360px).
- **Upgrade a Python package:** I activate the venv, run
  `pip install --upgrade <pkg>`, test the build, then `pip freeze > requirements.txt`,
  keep the explanatory comment at the top of the file, and commit.

## 10. Working from two computers

### Setting up my second computer
1. Install the tools and authenticate (sections 4.1 and 4.3).
2. Clone **outside OneDrive** (on my home computer the folder is
   `C:\Users\bymar\Desktop\Varios\Proyectos\AI Safety Web` instead; see
   section 4.2):
   ```powershell
   New-Item -ItemType Directory -Force C:\dev
   git clone https://github.com/Marcobm1/AiSafetyWeb.git C:\dev\AiSafetyWeb
   cd C:\dev\AiSafetyWeb
   ```
3. Set the local Git identity (section 4.4). `git clone` does not copy it.
4. Create the venv and install packages (section 4.5).

### My routine, every time
```powershell
cd C:\dev\AiSafetyWeb           # or my home-computer folder (section 4.2)
git pull                       # ALWAYS first
# ... work ...
git add -A
git commit -m "Describe the change in English"
git push                       # ALWAYS at the end
```

**Why `git pull` first is essential here:** the GitHub Action commits new data
**every day**. The remote will have new commits even if I haven't changed
anything. If I commit without pulling first, `git push` is rejected with
*"Updates were rejected because the remote contains work that you do not have
locally"*. I fix it with `git pull`, then `git push` again.

### Resolving a conflict
A conflict happens when the same lines of the same file changed both locally
and on GitHub. Here it would usually be in `data/`.

1. `git pull` reports `CONFLICT (content): Merge conflict in <file>`.
2. `git status` lists the conflicting files.
3. I open the file (VS Code highlights conflicts and offers *Accept Current /
   Incoming / Both*). The markers look like this:
   ```
   <<<<<<< HEAD
   my local version
   =======
   the version from GitHub
   >>>>>>> origin/main
   ```
   I edit the file so it contains the correct final content with no markers left.
4. `git add <file>` then `git commit` (Git proposes a merge message) and `git push`.

**Shortcut for data files:** `data/news/*.json` and `data/status.json` are
written by the robot, and I normally shouldn't edit them by hand. If they
conflict, I keep GitHub's version: `git checkout --theirs data/<file>` →
`git add data/<file>` → `git commit` → `git push`.

**Abort if unsure:** `git merge --abort` returns me to the state before the pull.

### Trying a change on a branch (so I can throw it away)

When I'm not sure I'll like a change, I don't make it on `main`. I make it on
a **branch**: a separate line of commits that starts from `main` and doesn't
affect it. If I like the result, I **merge** it into `main`; if not, I delete
the branch and `main` never knew it existed.

**Real example (23 Sep 2026):** I felt the design was a bit tight, so I tried
more spacing (bigger chapter titles, more air between sections and list
entries, a 660px column, 1.2rem text) on a branch called `design-spacing`. I
compared it side by side with `main` and decided to keep `main` as it was, so
I deleted the branch without merging.

**Seeing both versions at once, with a worktree.** A normal branch switch
(`git switch`) changes the files in my one folder, so I could only preview one
version at a time. A **worktree** is a second folder linked to the same
repository, with a different branch checked out. Each folder has its own
`_site/`, so I can serve both:

```powershell
cd C:\dev\AiSafetyWeb                     # or my home-computer folder
git pull
# 1. Create the branch from main, in a second folder next to the project
git worktree add -b design-spacing ..\AiSafetyWeb-spacing main

# 2. Make the changes in ..\AiSafetyWeb-spacing, then commit them there
cd ..\AiSafetyWeb-spacing
# ... edit static/css/style.css ...
git commit -am "Try more spacing"

# 3. Preview both: main on 8000 (terminal 1), the branch on 8001 (terminal 2)
#    terminal 1:  cd C:\dev\AiSafetyWeb;       .\.venv\Scripts\python.exe scripts\build_site.py --serve
#    terminal 2:  cd ..\AiSafetyWeb-spacing;   ..\AiSafetyWeb\.venv\Scripts\python.exe scripts\build_site.py --serve --port 8001
```

Then I open http://localhost:8000/AiSafetyWeb/ and
http://localhost:8001/AiSafetyWeb/ in two tabs and compare the same page.
(The branch folder uses the main folder's `.venv`; it doesn't need its own.
On my home computer the main folder is `AI Safety Web`, so the paths there
are like `& "..\AI Safety Web\.venv\Scripts\python.exe" scripts\build_site.py --serve --port 8001`
(quotes because of the spaces, and `&` to run a quoted path in PowerShell),
and I'd name the second folder `AI Safety Web-spacing`.)

**If I like it: merge, push, clean up.**
```powershell
# stop the 8001 preview (Ctrl+C in terminal 2)
cd C:\dev\AiSafetyWeb
git switch main
git pull
git merge design-spacing                  # brings the branch's commits into main
# update the docs (HOW_THIS_SITE_WORKS, DEVLOG) and commit them
git push
git worktree remove --force ..\AiSafetyWeb-spacing   # --force: the folder has a built _site/
git branch -d design-spacing              # -d only deletes a branch that is merged
```

**If I don't like it: throw it away (what I did with the spacing).**
```powershell
# stop the 8001 preview (Ctrl+C in terminal 2)
cd C:\dev\AiSafetyWeb
git worktree remove --force ..\AiSafetyWeb-spacing   # --force: the folder has a built _site/
git branch -D design-spacing              # -D (capital): delete even though it's not merged
```

**If I want something in between:** I keep editing and committing in the
branch folder, rebuild its preview, and compare again. Nothing reaches `main`
until I merge.

**Things to know:**
- I never pushed the branch, so it only ever existed on my computer. To try a
  branch on both computers I'd `git push -u origin design-spacing` and delete
  it on GitHub too when I'm done (`git push origin --delete design-spacing`).
- The worktree folder must be **outside OneDrive**, like the project.
- `git worktree list` shows which folders are linked; `git branch` shows my
  branches (the one with `*` is checked out in the current folder).
- The daily robot only commits to `main`, so it never touches my branch.

## 11. Common problems and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `git`/`python`/`gh` "not recognized" right after installing | The terminal was opened before installation | Close and reopen the terminal (or VS Code) |
| `python` opens the Microsoft Store | Windows "app execution alias" | Use `py -3.12`, or activate the venv; or disable the alias in Settings → Apps → Advanced app settings → App execution aliases |
| `Activate.ps1 cannot be loaded… running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use `.\.venv\Scripts\python.exe` directly |
| `git push` asks for a password / `Authentication failed` / 403 | Git is not authenticated | `gh auth login` (section 4.3) |
| `git push` rejected: "remote contains work…" | The daily Action pushed commits | `git pull`, then `git push` |
| Commits show the wrong author/email | Identity not set on this computer | `git config --local user.email ...` (section 4.4) |
| A source shows `"status": "error"` with `HTTPError: 404` in `status.json` | The site moved or removed its feed | Find the new feed URL (section 9, *Add a news source*) and update `config/sources.yaml` |
| `SSLError … HANDSHAKE_FAILURE` or timeouts for one site, only on my work computer | The company network/proxy blocks or intercepts that site | Nothing to fix if GitHub Actions can reach it; test at home or use an alternative feed URL (as I did for Google DeepMind) |
| `UnicodeEncodeError: 'charmap' codec…` when printing from my own Python snippets | The Windows console uses an old encoding | Set `$env:PYTHONIOENCODING = "utf-8"` in PowerShell first (`fetch_news.py` already handles this itself) |
| `HTTP 429, retrying in 30 s` for arXiv | Too many arXiv requests in a short time (e.g. many test runs) | Nothing: the script waits and retries. Avoid running it many times in a row |
| `BUILD FAILED: broken internal links` | A template has a hand-written link without the base path, or points to a page that doesn't exist | Use `url('...')` in the template and check the path (section 8) |
| `jinja2.exceptions.UndefinedError: '…' is undefined` | A typo in a template variable, or a value the build doesn't pass to that template | Fix the name in the template, or pass the value in `render(...)` |
| `OSError: [WinError 10048]` / "address already in use" with `--serve` | Another preview (or program) is using port 8000 | Stop the other one (`Ctrl+C` in its terminal) or use `--port 8001` |
| The preview shows an old version | The browser cached it | Rebuild and reload with `Ctrl+F5` |
| Justified paragraphs have big gaps between words | The browser has no English hyphenation dictionary yet (Chrome/Edge download it on first use), or the page lost `lang="en"` | Reload later; check `<html lang="en">` in `base.html` (it comes from `language:` in `config/site.yaml`) |
| The site stays dark (or light) although my system changed | I chose a theme with the header link; that choice wins | Click the link again, or clear the site's data in the browser |
| `warning: data/papers.yaml entry N (...) not published (no synopsis yet)` | The entry has no `synopsis`, or a `TODO` in it or in a required field | Write the synopsis / replace the `TODO`s (section 9). It's a warning, the rest of the site builds |
| `BUILD FAILED: ... unknown topic(s)`, `type must be one of`, `remove the tracking parameters`, `duplicate id(s)` | Broken data in `papers.yaml` (or an `id` also used in `books.yaml`) | Fix the field the message names (formats in section 3.1) |
| `BUILD FAILED: data/books.yaml ...: shelf '...' is not in shelves`, `olid must be ...`, `cover_id must be a number` | Broken data in `books.yaml` | Fix the field (section 3.1). The OLID is the edition's `OL…M`, not the work's `OL…W` |
| `BUILD FAILED: ... reading_log.yaml ...: month must be a month in quotes like "2026-09"` | The month was written without quotes | Write `month: "2026-09"` |
| `BUILD FAILED: ... via '...' is not an id in timeline.yaml` / `paper_ref ... is not a published entry` | A typo in the id, or the referenced entry isn't published yet (no synopsis) | Fix the id, or finish the referenced entry first |
| `warning: ... timeline.yaml ...: notes still have a TODO, not shown` | A placeholder note | Replace the `TODO(Marco)` with my notes; until then the stage shows without notes |
| `warning: ... start_here not in the path (no note yet)` | A `start_here` block without a note | Write the note |
| A book shows the typographic cover although it has `cover_id` | The cover id is wrong, or Open Library was unreachable | Open `https://covers.openlibrary.org/b/id/<cover_id>-M.jpg` in the browser; fix the id (section 9) |
| Clicking a book opens its page instead of the card | JavaScript is off or `library.js` failed, or the browser has no `<dialog>` support | Nothing breaks: the page shows the same card. Check DevTools → Console |
| `Not promoted: ... is not in paper_candidates.json` | Wrong candidate id, or the candidate expired (60 days) | Copy the exact `"id"` from the file; for an expired one, add the paper by hand |
| `Not promoted: already in papers.yaml as '...'` | That paper was promoted before | Nothing to do |
| The *To read / Read* buttons don't appear | JavaScript is off, or a script failed to load | Check DevTools → Console; without JS the buttons are hidden on purpose |
| A visitor's marks disappeared | They were in a private window, cleared their browser data, or used another browser/device | Marks live only in that browser; the export file is the backup (section 6.5) |
| Import says "not a shelf export from this site" | The file isn't an export from My shelf (or was edited into another format) | Export again from the original browser |
| The form says "Forbidden: the form token is missing or old" | The preview server was restarted after I opened the form | Reload the form page (my values are lost; copy them first) |
| The form says "Forbidden: wrong Host header" or "did not come from this preview" | I opened it through another address (e.g. my computer's network name), or something else posted to it | Open it as `http://localhost:8000/...` or `http://127.0.0.1:8000/...` |
| `BUILD FAILED: local-only form code found in the output` | A piece of the local form (`data-local-only` or a `/_local/` link) ended up in a published template or in `static/` | Remove it from that template/file: the form lives only in `scripts/local_form.py` and `templates/local/` |
| The Journal doesn't show a book | It's a book I'm reading without `started`, so it has no month yet | It's on the Bookshelf; add `started: "YYYY-MM"` to see it in the Journal |
| An email "Run failed: Update and deploy" | Every source failed, the data push couldn't be rebased, the build found a problem, or the deployment failed | Open the run from the email (or the Actions tab), click the red step and read its log. Fix the cause, then **Run workflow** again |
| The site shows *"This site may be out of date"* | No successful fetch for 48 h: the workflow is failing, disabled or GitHub is delayed | Check the Actions tab: a red run (see the row above) or a banner saying the workflow is disabled (see the next row) |
| The Actions tab says *"This scheduled workflow is disabled because there hasn't been activity in this repository for at least 60 days"* | GitHub's 60-day inactivity rule (it usually emails me before doing it) | Actions tab → **Update and deploy** → **Enable workflow** (the button in that banner), or `gh workflow enable update-and-deploy.yml`. Then **Run workflow** once so the site updates right away |
| The run fails at "Commit and push the data" with a rebase conflict | I edited a file in `data/` that the robot also changed the same day (usually `data/news/*.json` or `status.json`) | `git pull` on my computer, resolve the conflict (section 10: keep GitHub's version of the robot's files), push, then Run workflow |
| The run fails with *"…must be pinned to a full-length commit SHA"* or *"…is not allowed to be used"* | A `uses:` line with a tag instead of a SHA, or an action not made by GitHub | Pin it to the full SHA (section 7.3) or use an official `actions/…` action |
| The deploy job fails with a Pages error (404 or "Get Pages site failed") | Settings → Pages → Source is not "GitHub Actions" | Set it back to **GitHub Actions** (section 7.5) and re-run |
| The published site shows unstyled pages or 404s for `/static/...` | A link or asset without the base path | Can't happen with a green build (the link check would fail); if it does, check `base_path` in `config/site.yaml` |
| Redwood, Import AI, Zvi or Epoch fail with `403 Forbidden` only in GitHub Actions | Substack blocks requests from data-centre addresses (section 5.3) | Nothing to fix in the script; use an alternative feed of the same publication (test it with *check_feed*) or accept that source failing |
| A source keeps 0 items for days | Nothing new in 14 days, or `require_topic` filters everything out | Check the feed in a browser; adjust keywords or remove `require_topic` |

## 12. Possible future extensions

- **Public My Own Path pages for other people (with accounts).** Today every
  visitor's shelf is private to their browser, and My Own Path is only mine.
  A future version could let people sign in and publish their own path. That
  needs a server and a database (so no longer a purely static site), sign-in,
  privacy choices and moderation. The `ReadingStore` interface (section 6.5)
  is the hook: a server-backed store with the same methods could replace the
  localStorage one, and export/import already gives people a way to move
  their marks into an account.
- **Several people in My Own Path.** The Journal is already built with the
  person in mind: every month carries `data-person="<id>"` and the owner comes
  from `my_path.person` in `config/site.yaml`. A multi-person version would:
  keep one data folder per person (`data/my_path/<person>/timeline.yaml` and
  `reading_log.yaml`), list the people in `config/site.yaml`, build each
  person's Journal with the same `build_journal()`, and add a second
  drop-down (person) next to the month selector in `journal.js` that shows
  only that person's months. Without JavaScript, each person would get their
  own section (or page).
- **Visitors' own path (Timeline, Bookshelf and Journal).** First step, like
  My shelf: stored only in the visitor's browser (localStorage behind an
  interface like `ReadingStore`), with export/import to a JSON file, and the
  same Journal view built in the browser from that data. Second step, with
  accounts: a server-backed store with the same methods, so paths can be kept
  across devices and, if someone wants, published. That second step needs a
  server and a database, sign-in, privacy choices and moderation, so the site
  would no longer be purely static.
- **A hidden page to review paper candidates** (section 9).

## Glossary

- **API** — An interface through which a program requests data from a service (here the arXiv API returns paper listings as Atom/XML).
- **Atom** — A feed format similar to RSS.
- **`aria-pressed`** — An attribute that tells screen readers a button is a toggle and whether it is on (`true`) or off (`false`). The *To read / Read* buttons use it.
- **Base path** — The sub-folder a site lives under (`/AiSafetyWeb/`). All internal links must include it.
- **Blob** — A chunk of data created in the browser. My shelf puts the export JSON in a Blob and offers it as a download, without any server.
- **Branch / `main`** — A line of development in Git. `main` is the default and the one that is published. Other branches are for trying things without touching `main` (section 10).
- **Merge** — Bringing the commits of one branch into another (`git merge design-spacing` while on `main`).
- **Worktree** — A second folder linked to the same repository with another branch checked out, so two versions can be open (and previewed) at once.
- **CI/CD** — *Continuous Integration / Continuous Deployment*: automatically building, testing and publishing on every change or schedule. GitHub Actions is my CI/CD here.
- **Artifact** — A file (here a packed copy of `_site/`) that one job of a workflow uploads so another job can use it. The deploy job publishes the Pages artifact.
- **Clone** — Download a full copy of a repository, including its history.
- **Commit** — A saved snapshot of changes in Git, with a message and author.
- **Concurrency (workflow)** — A setting that stops two runs of a workflow from running at the same time; a new run waits for the current one.
- **Cron** — A syntax for schedules (`minute hour day month weekday`). `0 6 * * *` = every day at 06:00 UTC.
- **CSRF / Origin check** — *Cross-site request forgery*: a malicious website making my browser send a request to another site (here, my local form). Checking the `Origin` header (which site the request comes from) and a secret token stops it.
- **Deduplication** — Making sure the same item is saved only once, even if several feeds (or several runs) return it.
- **DNS rebinding** — An attack where a website's domain is switched to point to `127.0.0.1`, so a page from that site can talk to servers on my own computer. Checking the `Host` header defeats it: the browser still sends the attacker's domain.
- **Deploy** — Publish a built version of the site so visitors can see it.
- **Dry run** — Running a program so it shows what it would do without changing anything (`--dry-run`).
- **Exit code** — The number a program returns when it ends: 0 = success, anything else = failure. GitHub Actions marks a step as failed when it's not 0.
- **Drop cap** — A large first letter that spans several lines at the start of a chapter. Here only on pages that open with an introduction.
- **Escaping (autoescape)** — Turning characters like `<` into `&lt;` so text from outside can never become HTML or JavaScript on my page.
- **Focus ring (`:focus-visible`)** — The outline that shows which element the keyboard is on. `:focus-visible` shows it for keyboard use without adding it to mouse clicks.
- **Feed** — A machine-readable list of a site's latest posts (RSS or Atom).
- **Hash (SHA-1)** — A function that turns any text into a fixed-length fingerprint. The same input always gives the same hash, which makes it a handy stable id.
- **Hash (`#journal-2026-09`)** — The part of a URL after `#`. It points to a place inside the page and changes without reloading; the Journal keeps the chosen month there.
- **Hyphenation (`hyphens: auto`)** — The browser splits long words at line ends ("read-ings") using a dictionary for the page's language (`lang`). It keeps justified lines from opening big gaps.
- **`Host` header** — The part of an HTTP request that says which site the browser thinks it's talking to (`localhost:8000`).
- **HTTP status code** — The number a web server answers with: 200 = OK, 404 = not found, 403 = forbidden, 5xx = server error.
- **GitHub Actions** — GitHub's automation service. It runs *workflows* (YAML files) on GitHub's servers when triggered.
- **GitHub Pages** — GitHub's free hosting for static websites.
- **`GITHUB_TOKEN`** — A temporary credential that GitHub gives each workflow run so it can commit or deploy.
- **Jinja2** — A Python templating language: HTML files with placeholders like `{{ title }}` that a script fills with data.
- **JSON / YAML** — Text formats for structured data. JSON is strict and machine-friendly. YAML is more readable for hand-edited files.
- **Karma** — The community voting score of a LessWrong / Alignment Forum post. I use it as a noise filter.
- **localStorage** — A small key-value store inside the visitor's browser, per website. Private to that browser. It can be unavailable (private mode, blocked storage), which is why every access is wrapped in `try/catch`.
- **Merge conflict** — When Git cannot automatically combine two edits of the same lines.
- **Normalised URL** — A URL rewritten into one canonical form (https, lowercase host, no tracking parameters…) so two spellings of the same address compare as equal.
- **OIDC token (`id-token: write`)** — A short-lived, signed token that a workflow run can request to prove its identity to another service (here GitHub Pages), instead of storing a password or key.
- **`<dialog>`** — A native HTML element for pop-up windows. Opened with `showModal()`, it takes the focus, makes the rest of the page inert and closes with `Esc`. The Library's book cards use it.
- **`<details>` / `<summary>`** — A native HTML element that folds content away behind a clickable summary line, without any JavaScript. The timeline stages, the reading-log months and the synopses in Start Here use it.
- **`<template>`** — An HTML element whose content the browser parses but doesn't show or run; a script copies it when needed. The Library keeps each book's card in one.
- **Localhost / port** — `localhost` (127.0.0.1) means "this computer"; the port (8000) picks which program on it answers. The preview is only reachable from my own machine.
- **Open Library / Covers API / OLID** — Open Library is the Internet Archive's open book catalogue. Its Covers API serves cover images (`covers.openlibrary.org`). An OLID is its id for a book: `OL…M` for an edition, `OL…W` for a work.
- **OFL (SIL Open Font License)** — A free licence for fonts: they can be used, embedded and redistributed (not sold on their own), as long as the licence goes with them.
- **Pinned version** — An exact package version (`==`) so every install is identical (reproducible builds).
- **Progressive enhancement** — Building the page so it fully works as plain HTML, then adding JavaScript extras (like filters) on top. If the script fails, nothing essential breaks.
- **Pull / Push** — Download new commits from GitHub / upload my commits to GitHub.
- **SHA pinning** — Referring to an action by the full commit hash of its code (`@3d3c42e5…`) instead of a movable tag (`@v7`), so the code that runs can't change behind my back.
- **Slug** — A short, lowercase, URL-friendly identifier made of words and hyphens (`ai-2027`). I use slugs as the stable `id` of reading entries.
- **Remote / `origin`** — The copy of the repository on GitHub. `origin` is its conventional name.
- **`prefers-color-scheme`** — A CSS media query that tells the page whether the visitor's system is in light or dark mode.
- **Regular expression (regex)** — A small pattern language for searching text. The topic matcher turns each keyword into a regex such as `(?<!\w)AGI(?!\w)` ("AGI" as a whole word).
- **Self-hosted font** — A font file served by the site itself instead of a font service like Google Fonts, so visitors' browsers don't contact a third party.
- **Repository (repo)** — A project folder tracked by Git, including its full history.
- **RSS** — *Really Simple Syndication*: a standard XML format for publishing a list of recent posts.
- **Template inheritance** — In Jinja2, a page template `extends` a base template and only fills in the blocks that change, so the header and footer are written once.
- **XSS (cross-site scripting)** — An attack where text from an outside source ends up running as JavaScript in a visitor's browser. Autoescaping and the http(s)-only link filter protect against it.
- **Static site** — A website made of fixed files (HTML/CSS/JS) served as-is, with no server-side code or database. Fast, cheap (free here) and secure.
- **Static site generator** — A program that builds a static site from templates + data (mine is `scripts/build_site.py`).
- **User-Agent** — A header every HTTP request carries to say which program is asking. My script identifies itself as `AiSafetyWeb/1.0` with a link to the site, which is polite and what APIs like arXiv expect.
- **UTC** — Coordinated Universal Time, the time zone-free reference clock. All times in the data files are UTC.
- **Virtual environment (venv)** — A per-project folder with its own Python packages.
- **Workflow** — A YAML file in `.github/workflows/` that tells GitHub Actions what to run and when.
