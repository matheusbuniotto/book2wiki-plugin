---
description: Answer a question against the wiki — find relevant pages, synthesize an answer with citations, and offer to file good answers back as new pages so explorations compound. Use when the user asks a substantive question about material already in their wiki, "what does the wiki say about X", "compare X and Y across my books", or wants an analysis grounded in ingested sources.
---

# wiki-query

Answer questions against the persistent wiki and let valuable answers compound back into it.
This is the **Query** operation of the LLM-wiki pattern.

## First: load the schema

Read `${CLAUDE_PLUGIN_ROOT}/reference/schema.md` for page format and conventions before
filing anything back.

## Workflow

1. **Find candidate pages.** Read `wiki/index.md` first — it's the catalog. If a search tool
   exists (e.g. `bin/wiki-search`, or `qmd`), use it for larger wikis. Fall back to grep over
   `wiki/**/*.md`.
2. **Read the candidate pages** (and follow `[[wikilinks]]` to neighbours). Drill into the
   cited raw chapters only when the wiki pages are insufficient.
3. **Synthesize an answer with citations** — link to the wiki pages and raw sources you used.
   Pick the form that fits: prose, a comparison table, a list. Cross-book questions are where
   this wiki shines (e.g. "how do my data-systems and architecture books each treat trade-offs?").
4. **Offer to file it back.** A good comparison, analysis, or discovered connection shouldn't
   vanish into chat. Offer to save it as a new page with `type: query` frontmatter under the
   most relevant location (a shared `concepts/` page if cross-book). If filed: add it to
   `index.md`, cross-link it from related pages, and append a `## [date] query | <question>`
   entry to `log.md`.

## Rules

- Ground every claim in a cited page or raw source. If the wiki can't answer it, say so and
  suggest ingesting a source that would — don't fabricate.
- Filing back is an offer, not automatic, unless the user said to capture explorations.
