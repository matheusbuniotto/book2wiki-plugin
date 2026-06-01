---
description: Extract a PDF or EPUB into per-chapter markdown — the raw-source layer of a book2wiki. Use when the user wants to add a book/document to their wiki, "extract this PDF", "ingest this book" (run this first, then wiki-ingest), or convert a PDF/EPUB to markdown chapters.
---

# book-extract

Run the bundled `book2wiki` CLI (already on PATH while this plugin is enabled) to turn a
PDF or EPUB into per-chapter markdown. This produces the **immutable raw-source layer**
that `wiki-ingest` later reads from.

## Steps

1. Confirm the input file and where the library lives (default: current directory).
2. Run:
   ```bash
   book2wiki "$INPUT" --output-dir "$LIBRARY_DIR"
   ```
   - PDFs use the table of contents; pass `--max-level 2` for finer chapter splitting when
     the TOC is deeply nested and level-1 chapters come out too coarse.
3. The CLI prints the output folder and, on its last line, `SLUG: <book-slug>`. Capture that
   slug — it's the folder name (`<book-slug>/chapters/*.md` + `<book-slug>/index.md`).
4. Tell the user how many chapters were extracted and offer to run **wiki-ingest** on it.

## Notes

- Raw sources are immutable. Do not edit files under `<book-slug>/chapters/`.
- `$ARGUMENTS` may contain the file path the user passed; if empty, ask for it.

## Runtime

The `book2wiki` launcher needs a Python runtime and finds one automatically: it prefers `uv`
(zero setup), else builds a one-time cached virtualenv with the user's `python3`. First run
takes a few seconds; later runs are instant.

If `book2wiki` exits with "no Python runtime available", the user has neither `uv` nor
`python3`. Offer to install uv for them (one line, no admin) and then re-run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installing, `uv` lands in `~/.local/bin` — that may not be on PATH in the current
session, so either start a new shell or call `~/.local/bin/uv` for the very next run.
