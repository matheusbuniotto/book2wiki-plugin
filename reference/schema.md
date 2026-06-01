# book2wiki schema

This is the **schema** layer of the [LLM-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):
the conventions that make the LLM a disciplined wiki maintainer rather than a generic
chatbot. Every `book2wiki` skill reads this file. Follow it exactly, and evolve it (with
the user) as the wiki grows — a copy is written into each wiki root as `WIKI.md` on first
ingest so the wiki is self-describing even without the plugin.

## The three layers

1. **Raw sources** — `<book-slug>/chapters/*.md`, produced by the `book2wiki` CLI from a
   PDF/EPUB. **Immutable.** Read from them, cite them, never edit them.
2. **The wiki** — everything under `wiki/`. LLM-owned: concept pages, entity pages,
   overviews, comparisons, plus `index.md` and `log.md`. The user reads it; you write it.
3. **This schema** — page formats and workflows. Co-evolved with the user.

## Directory layout

The wiki gives you **two reading paths from the same files**: drill into one book, or
follow a concept across books.

```
wiki/
  WIKI.md              copy of this schema (self-describing wiki)
  index.md             master catalog of every page, by category  (you update every ingest)
  log.md               append-only timeline of ingests/queries/lints
  concepts/            SHARED cross-book concept pages
    consistency.md
    trade-offs.md
  books/
    <book-slug>/
      overview.md      synthesis of the whole book
      pages/           book-local concept/entity pages
        lsm-vs-btree.md
```

Raw sources live **outside** `wiki/` at `<book-slug>/chapters/`. The wiki references them
by relative markdown link; it does not copy them in.

## Linking conventions

- **Between wiki pages** use Obsidian `[[wikilinks]]` by page name (no path, no `.md`):
  `[[storage-engines]]`, `[[consistency]]`. These power graph view and backlinks.
- **A book-local page links UP to a shared concept** with a wikilink: a page in
  `books/ddia/pages/` says `see [[consistency]]` to reach `concepts/consistency.md`.
- **Citations into raw sources** use a relative markdown link with a locator, never a
  wikilink (raw chapters are outside the vault):
  `([Ch 3 — Storage and Retrieval](../../../designing-data-intensive-applications/chapters/14-chapter-3-storage-and-retrieval.md))`.
- Open `wiki/` as the Obsidian vault root for graph view; raw chapters appear as external links.
- **Page basenames must be unique across the whole vault** — Obsidian resolves `[[links]]` by
  filename, not folder, so two `overview.md` in different book folders would collide. Name a
  book's overview `<book-slug>-overview.md` (e.g. `ddia-overview.md`) and prefix any book-local
  page whose topic could recur in another book. Shared `concepts/` pages own the generic names
  (`consistency`, `storage-engines`); a book-local page on the same topic links UP to the shared
  one rather than re-using its name. Link with the basename or an `aliases:` value, never the
  `title`, since `title` frontmatter does not resolve wikilinks.

## Page format

Every wiki page starts with YAML frontmatter, then a body. Keep bodies tight and factual —
synthesis, not transcription. Every non-obvious claim must trace to a cited source.

```markdown
---
title: Storage Engines
type: concept            # concept | entity | overview | comparison | synthesis | query
books: [designing-data-intensive-applications]
tags: [storage, databases, indexing]
sources: 2               # how many raw sources contributed
updated: 2026-05-31
---

# Storage Engines

One-paragraph definition / thesis.

## Key ideas
- Bullet, each ending with a citation to the raw source it came from.

## Connections
- Contrasts with [[btrees]]; underpins [[oltp-vs-olap]].
- Cross-book: the same trade-off appears in [[trade-offs]].

## Sources
- [Ch 3 — Storage and Retrieval](../../../<book-slug>/chapters/14-...md)
```

Frontmatter rules:
- `type` is one of: `concept`, `entity`, `overview`, `comparison`, `synthesis`, `query`.
- `books` lists every book-slug that contributes — this is what makes a `concepts/` page
  cross-book. A page with two+ books in `books:` is a genuine cross-book hub.
- `updated` is ISO date; bump it on every edit.
- Dataview can query these fields, so keep names stable.

## index.md format

Content-oriented catalog. Organized by category. You read it first when answering a query,
then drill into pages. Update it on every ingest.

```markdown
# Wiki Index

## Concepts (shared)
- [[consistency]] — linearizability vs eventual; spans 2 books
- [[trade-offs]] — the recurring "no free lunch" theme

## Books
### Designing Data-Intensive Applications
- [[ddia-overview|Overview]]
- [[storage-engines]] — LSM vs B-tree, OLTP vs OLAP
```

## log.md format

Chronological, append-only. Every entry starts with a consistent prefix so
`grep "^## \[" wiki/log.md | tail -5` works:

```markdown
## [2026-05-31] ingest | Designing Data-Intensive Applications
- Extracted 29 chapters via book2wiki CLI.
- Created overview + 10 concept pages; seeded 4 shared concepts.
- Pages touched: storage-engines, replication, ... (12)
```

Entry types: `ingest`, `query`, `lint`.

## The three operations

**Ingest** — given a source (a book's chapters, or a single new chapter):
1. Read the raw source(s). For a whole book, read `index.md`/TOC first, then chapters.
2. Discuss key takeaways with the user (unless told to batch silently).
3. Write/update pages: a book `overview.md`, book-local concept/entity pages, and update or
   create the shared `concepts/` pages the new material touches. One source may touch 10–15
   pages — that bookkeeping is the whole point; do it thoroughly.
4. Maintain cross-references both directions (link the new page from related pages too).
5. Update `index.md`. Append a `log.md` entry.

**Query** — given a question:
1. Read `index.md` to find candidate pages; if a `bin/wiki-search` exists, use it.
2. Read those pages, synthesize an answer **with citations** to pages and raw sources.
3. Offer to file a good answer back as a new page (`type: query`) — explorations should
   compound, not vanish into chat. If filed, update `index.md` + `log.md`.

**Lint** — health-check the wiki:
- Contradictions between pages; stale claims a newer source supersedes.
- Orphan pages (no inbound `[[links]]`); concepts mentioned but lacking their own page.
- Missing cross-references; data gaps a web search could fill.
- Report findings + suggested fixes/questions; apply fixes the user approves. Log it.

## Principles

- You do the bookkeeping; the user curates sources and asks questions.
- Never invent claims. If the source doesn't support it, say so or flag a gap.
- Prefer updating an existing page over creating a near-duplicate (lint catches dupes).
- The wiki is a git repo of markdown — small, reviewable commits per ingest are ideal.
