# book2wiki

A Claude Code plugin that turns your **PDFs and EPUBs into a living, interlinked wiki** that
the LLM builds and maintains for you — based on Andrej Karpathy's
[LLM-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Instead of re-deriving knowledge from raw documents on every question (RAG), the LLM
**compiles a persistent wiki once and keeps it current**: concept pages, entity pages,
cross-references, and a synthesis that gets richer with every source you add. You curate and
ask questions; the LLM does the summarizing, cross-referencing, and bookkeeping.

## What's inside

| Component | What it does |
|---|---|
| `book2wiki` (CLI on PATH) | Extract a PDF/EPUB into per-chapter markdown — the immutable raw-source layer |
| `/book2wiki:book-extract` | Run the extractor on a file |
| `/book2wiki:wiki-ingest` | Read a source → write interlinked pages, update the shared concept layer, `index.md`, `log.md` |
| `/book2wiki:wiki-query` | Answer questions against the wiki with citations; file good answers back |
| `/book2wiki:wiki-lint` | Find contradictions, orphans, stale claims, gaps; propose fixes |

The wiki is plain markdown with `[[wikilinks]]` and YAML frontmatter — open the `wiki/`
folder in **Obsidian** for graph view and backlinks, and it's a git repo so you get history
for free. The conventions live in [`reference/schema.md`](reference/schema.md) and a
copy is written into each wiki as `WIKI.md`, so a wiki stays self-describing without the plugin.

## Install

```
/plugin marketplace add matheusbuniotto/book2wiki-plugin
/plugin install book2wiki@book2wiki
```

Or test locally without installing:

```
claude --plugin-dir ./book2wiki-plugin
```

Requires [`uv`](https://docs.astral.sh/uv/) (the extractor is a self-contained uv script;
dependencies install automatically on first run).

## Usage

```
# 1. Extract a book into raw markdown chapters
/book2wiki:book-extract ~/books/designing-data-intensive-applications.pdf

# 2. Build / grow the wiki from it
/book2wiki:wiki-ingest designing-data-intensive-applications

# 3. Ask questions; compound the answers back in
/book2wiki:wiki-query how do my books each handle consistency trade-offs?

# 4. Keep it healthy as it grows
/book2wiki:wiki-lint
```

Resulting layout (two reading paths from the same files — drill into a book, or follow a
concept across books):

```
designing-data-intensive-applications/   raw sources (immutable)
  chapters/*.md
wiki/
  WIKI.md            self-describing schema
  index.md           catalog of every page
  log.md             append-only timeline
  concepts/          shared cross-book concept pages
  books/
    designing-data-intensive-applications/
      overview.md
      pages/*.md      book-local pages, linking up to concepts/
```

## The pattern in one line

> Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase. — Karpathy

You're in charge of sourcing and asking the right questions. The plugin makes Claude a
disciplined wiki maintainer that does the grunt work — the bookkeeping humans abandon.

## License

MIT
