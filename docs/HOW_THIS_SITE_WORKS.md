# How This Site Works

> These are my notes on the **current** state of the project. I update them in
> the same commit as every change. Sections marked **🚧 Not built yet** describe
> the design I agreed on for a future stage.
>
> I wrote them for someone with a technical background (my own is security
> operations) who is new to web development. Unfamiliar terms are defined in the
> [Glossary](#glossary).

**Current status:** Stage 4a complete (Papers, reading tracker, My shelf with export/import, `promote_candidate.py`). Next: Stage 4b (the Library of books). The plan for the remaining stages is in [docs/DEVLOG.md](DEVLOG.md).

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
| **Library** 🚧 4b | Books only, on themed shelves, each shown with its real cover (Open Library). Clicking a book opens its card | `data/books.yaml`, which I edit by hand |
| **Start Here** 🚧 5 | An ordered reading path for newcomers to AI Safety, in stages, each entry with a note on why it sits at that point | Also `data/papers.yaml`: the stage list plus a `start_here` block on each entry in the path |
| **My Own Path** 🚧 5 | My public learning log: a **Timeline** of courses, projects and milestones, a **Reading log** grouped by month, and a **Bookshelf** of the books I read, with my opinion | `data/my_path/timeline.yaml` and `data/my_path/reading_log.yaml`, which I edit by hand |
| **Reading tracker** | Each visitor marks entries as *To read* / *Read* (in Papers, and later in the Library and Start Here) | The visitor's own browser (localStorage) |
| **My shelf** | The visitor's own marks in one page, with **Export / Import** to back them up or move them to another browser | The visitor's own browser (localStorage) |
| **About** | What the site is, sources, how updates work | Template text |

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
| `data/papers.yaml` | Papers: my curated papers, essays, reports, scenarios and posts (12 so far); also the Start Here stage list | ✅ |
| `data/books.yaml` | Library: books on themed shelves | 🚧 Stage 4b |
| `data/my_path/timeline.yaml` | My Own Path timeline (my first two courses) | ✅ data, 🚧 page in Stage 5 |
| `data/my_path/reading_log.yaml` | My Own Path reading log (empty, format in comments) | ✅ data, 🚧 page in Stage 5 |
| `scripts/promote_candidate.py` | Copies a candidate into `papers.yaml` as a new block | ✅ |
| `scripts/build_site.py` | Turns templates + data into the `_site/` folder, checks links, local preview | ✅ |
| `templates/` | Jinja2 HTML templates (`base.html`, `_macros.html`, one per page type) | ✅ (more pages in Stages 4–5) |
| `static/css/style.css` | Basic layout | ✅ basic (design in Stage 6) |
| `static/js/filters.js` | Filter menus for news and papers | ✅ |
| `static/js/reading-store.js`, `tracker.js`, `my-shelf.js` | Reading tracker: the `ReadingStore`, the *To read / Read* buttons, the My shelf page with export/import | ✅ |
| `.github/workflows/update-and-deploy.yml` | Daily automation | 🚧 Stage 7 |
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

#### `data/books.yaml` — the Library (🚧 Stage 4b, format agreed)

```yaml
shelves:                               # order in this list = order on the site
  - id: ai-safety                      # referenced by `shelf` below
    title: AI Safety & Alignment

entries:
  - id: human-compatible               # unique across papers.yaml and books.yaml
    title: "Human Compatible: Artificial Intelligence and the Problem of Control"
    authors: ["Stuart Russell"]
    year: 2019                         # year of the edition I list
    edition: "..."                     # optional, e.g. "2nd edition"
    shelf: ai-safety
    olid: OL...M                       # Open Library edition id (verified)
    cover_id: 1234567                  # Open Library cover id (preferred for the image)
    isbn: "978..."                     # optional, reference only (never used to load covers)
    url: https://openlibrary.org/works/OL...W   # the book's page ("book page" link)
    free_url: https://...              # optional: ONLY an official free version by the authors/publisher
    synopsis: >                        # REQUIRED to publish
      ...
    why_it_matters: >                  # optional
      ...
    my_opinion: >                      # optional, only mine
      ...
    added: 2026-09-23
```

- **Edition:** always the most recent English edition, verified on Open Library.
- **Covers** come straight from Open Library's Covers API as the image `src`
  (`https://covers.openlibrary.org/b/id/<cover_id>-M.jpg`, or `/b/olid/<olid>-M.jpg`).
  I never download them into the repo. I use the cover id or OLID, not the ISBN,
  because ISBN lookups are limited to 100 requests every 5 minutes per IP
  address. A book without a cover gets a typographic cover drawn in the site's
  style. The book card and the About page link to Open Library as a courtesy.
- **`free_url`** is shown as "Free version (official)". Only for versions the
  authors or publisher publish for free themselves, never unauthorised copies.
- **Planned shelves:** AI Safety & Alignment; AI, Society & Governance; Machine
  Learning & Deep Learning; Mathematics for ML; Programming & Python; Thinking &
  Rationality.

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
`last_run` for its "data is stale" warning (Stage 7).

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

#### `data/my_path/` — My Own Path (edited by hand)

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
    type: essay                 # paper | report | essay | article | book | resource
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

Rules the build script will check (Stage 5), failing with a clear message:
`month` must look like `YYYY-MM`; `via` must be an `id` in `timeline.yaml`;
`paper_ref` must be an `id` in `papers.yaml` and `book_ref` one in
`books.yaml`; a finished book needs `month`; an entry without a ref needs
`title`, `author`, `source` and `url`; no URL may contain `utm_` parameters.

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
I keep the project at **`C:\dev\AiSafetyWeb`**. OneDrive (and similar sync tools)
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
- **Google DeepMind:** its own feed (`deepmind.google/blog/rss.xml`) fails from
  my work network (TLS handshake blocked), so for now I use the one on
  `blog.google`. In Stage 7 I'll test the DeepMind feed from GitHub Actions and
  switch to it if it works there.
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
   | `my-shelf/index.html` | `my_shelf.html` | My shelf: the visitor's marks, and export/import |
   | `about/index.html` | `about.html` | What the site is, the source list (from `sources.yaml`) and the result of the last fetch (from `status.json`) |
   | `404.html` | `404.html` | "Page not found". GitHub Pages shows it for any unknown address |

   Before rendering, `papers.yaml` is **validated** and the publishing rule is
   applied (section 3.1). Skipped entries are listed as `warning: ... not
   published (...)`; broken data stops the build with `BUILD FAILED`.
4. **Check every internal link** (section 8). If one is broken, the build stops
   with `BUILD FAILED` and a list of the bad links, so a broken site never gets
   published.

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
  (the *To read / Read* buttons of one entry, keyed by its `id`).
- The menu comes from `nav:` in `config/site.yaml`: News · Papers · About for
  now; Library, Start Here and My Own Path join it when their pages exist.
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

Three small scripts, loaded only on the pages that need them (Papers and My
shelf), in this order:

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
3. **`my-shelf.js` — My shelf.** The page contains a hidden catalogue of every
   published entry. The script **moves** the marked ones into the *To read*
   and *Read* lists (moving, not copying, so no element exists twice) and back
   when a mark is removed. Marks for entries that aren't on the site right now
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

### 6.6 Styles

`static/css/style.css` is a simple, readable layout for now (system font,
~44rem column, wraps long titles so there's never horizontal scrolling on a
phone). The real design (serif type, 680px reading column, light/dark themes)
is Stage 6.

## 7. GitHub Actions and the cron schedule

🚧 **Not built yet (Stage 7).** The design I agreed on: a **single** workflow
`update-and-deploy.yml`, triggered by a daily cron, by a manual button and by
every push to `main`. It fetches, commits the data, builds and deploys.

I use one workflow and not two because commits made by a workflow (with the
built-in `GITHUB_TOKEN`) **do not trigger other workflows**. A separate
"deploy on push" workflow would never see the robot's commits.

**60-day inactivity rule:** GitHub disables scheduled workflows in public
repositories after 60 days without repository activity. My safeguards:
- `data/status.json` is committed on every run, so there is activity every day.
- The site shows a visible warning if the last update is older than 48 hours.
  This check runs in the visitor's browser, so it still works if Actions stops.
- GitHub emails me when a workflow run fails.

**To do in Stage 7:** test Google DeepMind's own feed
(`https://deepmind.google/blog/rss.xml`) from GitHub Actions. It fails only from
my work network, so if it works on GitHub's servers I'll switch to it
(section 5.3).

## 8. Deployment to GitHub Pages and the base path

🚧 **Deployment details in Stage 7.** The base-path handling is built (Stage 3).

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
  3. Run `python scripts\fetch_news.py --dry-run` and check the new source's
     line says `ok` and keeps a sensible number of items.
  4. Run it for real (or let the daily bot do it), update the source table in
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
- **Add a book to the Library** (🚧 Stage 4b; format in section 3.1):
  1. Find the book on **openlibrary.org** and open its **most recent English
     edition**. Verify title, authors, year and publisher against the
     publisher's or author's page.
  2. From the edition page, copy the **edition OLID** (the `OL…M` in the URL)
     and the **cover id** (right-click the cover → copy image address: it's the
     number in `covers.openlibrary.org/b/id/<number>-L.jpg`). I check the
     cover opens. No cover → leave `cover_id` out; the site draws a
     typographic cover.
  3. Choose the `shelf` and an `id` not used in `papers.yaml` or `books.yaml`,
     and add the block to `data/books.yaml`. `url` is the book's Open Library
     page. Add `free_url` only if the authors or publisher offer the full book
     for free themselves.
  4. Write the `synopsis` (2–4 neutral sentences, my own words), optionally
     `why_it_matters` and `my_opinion`. Build, commit and push.
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
- **Add an entry to the Start Here path:** 🚧 Stage 5 (add a `start_here` block to
  an entry in `papers.yaml`, after verifying the entry against the original source).
- **Add a reading to My Own Path** (the file exists now; the page comes in Stage 5):
  1. Open the original and **verify** the exact title, the author(s), the
     publication and the URL. I remove any `utm_…` parameters from the URL.
  2. If it's a paywalled article, I look for an archived copy (for example on
     the Wayback Machine, `web.archive.org`) and keep its URL for `archive_url`.
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
     `type` is one of paper, report, essay, article, book, resource. `via` is
     the `id` of a stage in `timeline.yaml`.
  5. (From Stage 3 on) run `python scripts\build_site.py` to check nothing is
     broken, then commit and push. The site updates on the next deploy.
- **Add a stage to the My Own Path Timeline:** add a block at the top of
  `data/my_path/timeline.yaml` with a new `id` (short slug that I never change),
  `type` (course, project or milestone), `date`, `title`, `status` and, when
  I have them, `provider`, `url` and `notes`. When I finish it, I add
  `completed: YYYY-MM-DD` and change `status` to `completed`.
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
- **Change the design:** 🚧 Stage 6 (edit `static/css/style.css`).
- **Upgrade a Python package:** I activate the venv, run
  `pip install --upgrade <pkg>`, test the build, then `pip freeze > requirements.txt`,
  keep the explanatory comment at the top of the file, and commit.

## 10. Working from two computers

### Setting up my second computer
1. Install the tools and authenticate (sections 4.1 and 4.3).
2. Clone **outside OneDrive**:
   ```powershell
   New-Item -ItemType Directory -Force C:\dev
   git clone https://github.com/Marcobm1/AiSafetyWeb.git C:\dev\AiSafetyWeb
   cd C:\dev\AiSafetyWeb
   ```
3. Set the local Git identity (section 4.4). `git clone` does not copy it.
4. Create the venv and install packages (section 4.5).

### My routine, every time
```powershell
cd C:\dev\AiSafetyWeb
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
| `warning: data/papers.yaml entry N (...) not published (no synopsis yet)` | The entry has no `synopsis`, or a `TODO` in it or in a required field | Write the synopsis / replace the `TODO`s (section 9). It's a warning, the rest of the site builds |
| `BUILD FAILED: ... unknown topic(s)`, `type must be one of`, `remove the tracking parameters`, `duplicate id(s)` | Broken data in `papers.yaml` (or an `id` also used in `books.yaml`) | Fix the field the message names (formats in section 3.1) |
| `Not promoted: ... is not in paper_candidates.json` | Wrong candidate id, or the candidate expired (60 days) | Copy the exact `"id"` from the file; for an expired one, add the paper by hand |
| `Not promoted: already in papers.yaml as '...'` | That paper was promoted before | Nothing to do |
| The *To read / Read* buttons don't appear | JavaScript is off, or a script failed to load | Check DevTools → Console; without JS the buttons are hidden on purpose |
| A visitor's marks disappeared | They were in a private window, cleared their browser data, or used another browser/device | Marks live only in that browser; the export file is the backup (section 6.5) |
| Import says "not a shelf export from this site" | The file isn't an export from My shelf (or was edited into another format) | Export again from the original browser |
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
- **A hidden page to review paper candidates** (section 9).

## Glossary

- **API** — An interface through which a program requests data from a service (here the arXiv API returns paper listings as Atom/XML).
- **Atom** — A feed format similar to RSS.
- **`aria-pressed`** — An attribute that tells screen readers a button is a toggle and whether it is on (`true`) or off (`false`). The *To read / Read* buttons use it.
- **Base path** — The sub-folder a site lives under (`/AiSafetyWeb/`). All internal links must include it.
- **Blob** — A chunk of data created in the browser. My shelf puts the export JSON in a Blob and offers it as a download, without any server.
- **Branch / `main`** — A line of development in Git. `main` is the default and the one that is published.
- **CI/CD** — *Continuous Integration / Continuous Deployment*: automatically building, testing and publishing on every change or schedule. GitHub Actions is my CI/CD here.
- **Clone** — Download a full copy of a repository, including its history.
- **Commit** — A saved snapshot of changes in Git, with a message and author.
- **Cron** — A syntax for schedules (`minute hour day month weekday`). `0 6 * * *` = every day at 06:00 UTC.
- **Deduplication** — Making sure the same item is saved only once, even if several feeds (or several runs) return it.
- **Deploy** — Publish a built version of the site so visitors can see it.
- **Dry run** — Running a program so it shows what it would do without changing anything (`--dry-run`).
- **Exit code** — The number a program returns when it ends: 0 = success, anything else = failure. GitHub Actions marks a step as failed when it's not 0.
- **Escaping (autoescape)** — Turning characters like `<` into `&lt;` so text from outside can never become HTML or JavaScript on my page.
- **Feed** — A machine-readable list of a site's latest posts (RSS or Atom).
- **Hash (SHA-1)** — A function that turns any text into a fixed-length fingerprint. The same input always gives the same hash, which makes it a handy stable id.
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
- **`<dialog>`** — A native HTML element for pop-up windows: keyboard accessible and closed with `Esc`. The Library's book cards will use it (Stage 4b).
- **Localhost / port** — `localhost` (127.0.0.1) means "this computer"; the port (8000) picks which program on it answers. The preview is only reachable from my own machine.
- **Open Library / Covers API / OLID** — Open Library is the Internet Archive's open book catalogue. Its Covers API serves cover images (`covers.openlibrary.org`). An OLID is its id for a book: `OL…M` for an edition, `OL…W` for a work.
- **Pinned version** — An exact package version (`==`) so every install is identical (reproducible builds).
- **Progressive enhancement** — Building the page so it fully works as plain HTML, then adding JavaScript extras (like filters) on top. If the script fails, nothing essential breaks.
- **Pull / Push** — Download new commits from GitHub / upload my commits to GitHub.
- **Slug** — A short, lowercase, URL-friendly identifier made of words and hyphens (`ai-2027`). I use slugs as the stable `id` of reading entries.
- **Remote / `origin`** — The copy of the repository on GitHub. `origin` is its conventional name.
- **Regular expression (regex)** — A small pattern language for searching text. The topic matcher turns each keyword into a regex such as `(?<!\w)AGI(?!\w)` ("AGI" as a whole word).
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
