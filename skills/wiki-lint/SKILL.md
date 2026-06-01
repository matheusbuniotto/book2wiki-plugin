---
description: Health-check the wiki — find contradictions, stale claims, orphan pages, missing concept pages, missing cross-references, and data gaps, then propose fixes. Use when the user says "lint the wiki", "check the wiki health", "find orphans/contradictions", or periodically after several ingests.
---

# wiki-lint

Periodically keep the wiki healthy as it grows. This is the **Lint** operation of the
LLM-wiki pattern. Report findings, then apply the fixes the user approves.

## First: load the schema

Read `${CLAUDE_PLUGIN_ROOT}/reference/schema.md` for the conventions you're checking against.

## Checks

Scan `wiki/**/*.md` and report, grouped:

1. **Contradictions** — pages making incompatible claims. Quote both and cite their sources.
2. **Stale claims** — a page superseded by a newer source (check `log.md` order and `updated`
   dates). Flag for revision.
3. **Orphans** — pages with no inbound `[[wikilinks]]` (nothing reaches them but the index).
   Suggest where to link them from.
4. **Missing pages** — concepts referenced via `[[link]]` that have no page yet, or important
   concepts discussed in sources but never given a page.
5. **Missing cross-references** — related pages that should link each other but don't;
   especially book-local pages that should link UP to a shared `concepts/` page.
6. **Data gaps** — open questions or thin pages a web search or a new source could fill.
   Suggest specific sources/questions.
7. **Schema drift** — frontmatter missing required fields, broken citation links, `index.md`
   entries pointing at deleted pages.

## Output

- A concise findings report grouped by the categories above, each with a concrete suggested fix.
- Ask which fixes to apply. Apply the approved ones (create stub pages, add links, revise
  stale claims, repair the index).
- Append a `## [date] lint | <summary>` entry to `log.md` recording what was found and fixed.

## Rules

- Suggest; don't silently rewrite. The user steers what the wiki should emphasize.
- A good lint also proposes new questions to investigate and sources to look for.
