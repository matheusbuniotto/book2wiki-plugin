---
description: Ingest a source (a book's chapters, or one new chapter/document) into the persistent wiki — read it, write interlinked concept/entity pages, update the shared concept layer, and maintain index.md + log.md. Use when the user says "ingest", "add this to the wiki", "file this", "build the wiki for X", or after book-extract produces chapters.
---

# wiki-ingest

You are the wiki maintainer. Integrate a new source into a persistent, interlinked wiki —
don't just summarize it. This is the **Ingest** operation of the LLM-wiki pattern.

## First: load the schema

Read `${CLAUDE_PLUGIN_ROOT}/reference/schema.md` in full. It defines the directory
layout, page format, frontmatter, linking conventions, and the index.md/log.md formats.
Follow it exactly. On the very first ingest into a wiki, copy it to `wiki/WIKI.md` so the
wiki is self-describing.

## Workflow

1. **Locate the wiki.** Default `wiki/` in the current project; create it if missing
   (`wiki/concepts/`, `wiki/books/`, `index.md`, `log.md`, `WIKI.md`).
2. **Read the source.** For a whole book, read its `<book-slug>/index.md` (the TOC) first to
   get the shape, then read the chapters under `<book-slug>/chapters/`. For a single new
   chapter/document, read just that. Read raw text — never trust a prior summary as ground truth.
3. **Discuss takeaways** with the user and confirm emphasis — unless they asked to
   batch-ingest silently, in which case proceed.
4. **Write pages** (see schema for exact format + frontmatter):
   - `books/<slug>/overview.md` — synthesis of the book/source.
   - `books/<slug>/pages/*.md` — one page per substantial concept or entity. Cite raw
     chapters for every non-obvious claim.
   - Update or create **shared** `concepts/*.md` for concepts that recur or will recur across
     books. Add the new book-slug to the page's `books:` frontmatter; a page with 2+ books is
     a true cross-book hub. Book-local pages link UP to these with `[[wikilinks]]`.
5. **Cross-reference both directions.** When page A links B, make sure B (or the index)
   reaches back. Add `## Connections` links to neighbours.
6. **Update `index.md`** — add every new page under the right category with a one-line summary.
7. **Append a `log.md` entry** — `## [YYYY-MM-DD] ingest | <source title>` plus what you did
   and which pages you touched.
8. **Offer to commit** the wiki changes (it's a git repo of markdown; small per-ingest commits
   are ideal).

## Rules

- Synthesis, not transcription. Tight, factual pages where every claim traces to a citation.
- Never invent. If the source doesn't support a claim, omit it or flag a gap for lint.
- Prefer updating an existing page over creating a near-duplicate.
- One source legitimately touches 10–15 pages. The bookkeeping IS the value — do it fully.
