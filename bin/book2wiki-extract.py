#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ebooklib>=0.20",
#     "html2text>=2025.4.15",
#     "pymupdf>=1.27.2.3",
# ]
# ///
"""book2wiki — convert a PDF/EPUB into per-chapter markdown (the wiki's raw-source layer).

Self-contained: run directly thanks to uv's inline script metadata. When this plugin
is enabled, `book2wiki` is on the Bash PATH, so skills can shell out to it.

    book2wiki path/to/book.pdf --output-dir ./library
"""
import argparse
import re
import sys
from pathlib import Path

import ebooklib
import fitz  # pymupdf
import html2text
from ebooklib import epub


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def clean_markdown(text: str) -> str:
    # Rejoin words split across visual lines with a hyphen (soft or regular)
    text = re.sub(r"(\w)[‐-]\n\n?(\w)", r"\1\2", text)
    # Join wrapped prose: previous line doesn't end in sentence punctuation,
    # next (possibly blank-line-separated) line starts lowercase.
    # Handles both single \n and \n\n because pymupdf wraps each visual line
    # in its own <p>, which html2text renders with double newlines.
    text = re.sub(r"(?<=[^.!?:\n])\n\n?(?=[a-z\(\"'—])", " ", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── PDF ──────────────────────────────────────────────────────────────────────


def pdf_title(doc: fitz.Document, path: Path) -> str:
    meta = doc.metadata or {}
    title = (meta.get("title") or "").strip()
    return title if title else path.stem


def pdf_chapters(doc: fitz.Document, max_level: int) -> list[tuple[str, int, int]]:
    toc = [entry for entry in doc.get_toc() if entry[0] <= max_level]
    if not toc:
        return [("document", 0, doc.page_count - 1)]

    chapters = []
    for i, (_, title, start_page) in enumerate(toc):
        start = start_page - 1  # pymupdf pages are 0-indexed, toc is 1-indexed
        end = (toc[i + 1][2] - 2) if i + 1 < len(toc) else doc.page_count - 1
        if start > end:
            end = start
        chapters.append((title, start, end))
    return chapters


def block_text_size(block: dict) -> tuple[str, int]:
    # Flatten a dict-mode block into one paragraph + its dominant font size.
    line_strs = []
    size_chars: dict[int, int] = {}
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        line_strs.append("".join(s["text"] for s in spans))
        for s in spans:
            sz = round(s["size"])
            size_chars[sz] = size_chars.get(sz, 0) + len(s["text"])
    text = "\n".join(line_strs)
    text = re.sub(r"(\w)[‐-]\n(\w)", r"\1\2", text)  # rejoin hyphen breaks inside block
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    size = max(size_chars, key=size_chars.get) if size_chars else 0
    return text, size


def page_blocks(page: fitz.Page, margin: float = 0.08) -> list[tuple[str, int, bool]]:
    # Returns (text, font_size, in_margin). in_margin = sits in the header/footer band;
    # carried through so the running-head filter can require "repeats AND edge-dwelling".
    height = page.rect.height
    top, bottom = height * margin, height * (1 - margin)
    out = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:  # skip images
            continue
        y0, y1 = block["bbox"][1], block["bbox"][3]
        center = (y0 + y1) / 2
        in_margin = center < top or center > bottom
        text, size = block_text_size(block)
        if text:
            out.append((text, size, in_margin))
    return out


def is_running_header(text: str) -> bool:
    t = text.strip()
    if re.fullmatch(r"\d+", t):  # bare page number
        return True
    if re.match(r"^\d+\s*\|", t):  # "24 | Chapter 2: ..."
        return True
    if re.search(r"\|\s*\d+$", t):  # "Technical Breadth | 25"
        return True
    return False


def format_block(text: str, size: int, body_size: int) -> str:
    # Headings are short blocks meaningfully larger than body text. Ratios (not absolute
    # deltas) so this travels across books with different base font sizes.
    if size >= body_size * 1.2 and len(text.split()) <= 14:
        return ("## " if size >= body_size * 1.5 else "### ") + text
    return text


def join_blocks(blocks: list[str]) -> str:
    # Merge blocks where a word is hyphenated across a block or page boundary.
    merged: list[str] = []
    for block in blocks:
        if merged and merged[-1].endswith(("‐", "-")):
            prev = merged[-1][:-1]
            sep = "" if prev[-1:].isalpha() else " "
            merged[-1] = prev + sep + block
        else:
            merged.append(block)
    return "\n\n".join(merged).strip()


def drop_running_heads(blocks: list[tuple[str, int, bool]]) -> list[tuple[str, int, bool]]:
    # A running head/foot is a short line that repeats across pages AND usually sits
    # in the margin band. The margin condition protects real recurring body labels
    # ("Summary", "Exercises") that repeat but live in the text column.
    total = {}
    margin = {}
    for text, _size, in_margin in blocks:
        total[text] = total.get(text, 0) + 1
        if in_margin:
            margin[text] = margin.get(text, 0) + 1

    def is_running(text: str) -> bool:
        return (
            len(text.split()) <= 8
            and total[text] >= 4
            and margin.get(text, 0) * 2 >= total[text]  # in margin on most occurrences
        )

    return [b for b in blocks if not is_running(b[0])]


def extract_pdf(input_path: Path, output_path: Path, max_level: int) -> tuple[str, str, list[str]]:
    doc = fitz.open(input_path)
    title = pdf_title(doc, input_path)
    author = (doc.metadata or {}).get("author", "").strip()

    chapters = pdf_chapters(doc, max_level)
    chapter_files = []

    for n, (chapter_title, start, end) in enumerate(chapters, 1):
        raw = []  # (text, size, in_margin)
        for p in range(start, end + 1):
            raw.extend(page_blocks(doc[p]))
        raw = [b for b in raw if not is_running_header(b[0])]

        raw = drop_running_heads(raw)

        # body_size = most common font size weighted by character count
        size_chars: dict[int, int] = {}
        for t, s, _ in raw:
            size_chars[s] = size_chars.get(s, 0) + len(t)
        body_size = max(size_chars, key=size_chars.get) if size_chars else 0

        formatted = [format_block(t, s, body_size) for t, s, _ in raw]
        content = join_blocks(formatted)
        fname = write_chapter(output_path, n, chapter_title, content)
        chapter_files.append((chapter_title, fname))

    doc.close()
    return title, author, chapter_files


# ── EPUB ─────────────────────────────────────────────────────────────────────


def epub_title(book: epub.EpubBook, path: Path) -> str:
    title = book.get_metadata("DC", "title")
    if title:
        return title[0][0].strip()
    return path.stem


def epub_author(book: epub.EpubBook) -> str:
    authors = book.get_metadata("DC", "creator")
    if authors:
        return authors[0][0].strip()
    return ""


def html_to_title(html_bytes: bytes) -> str:
    text = html_bytes.decode("utf-8", errors="replace")
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", text, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def extract_epub(input_path: Path, output_path: Path) -> tuple[str, str, list[str]]:
    book = epub.read_epub(str(input_path))
    title = epub_title(book, input_path)
    author = epub_author(book)

    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = False
    h.body_width = 0  # no line wrapping

    chapter_files = []
    n = 0
    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        html_bytes = item.get_content()
        if b"<nav" in html_bytes:
            continue
        content = clean_markdown(h.handle(html_bytes.decode("utf-8", errors="replace")))
        if not content:
            continue
        n += 1
        chapter_title = html_to_title(html_bytes) or Path(item.file_name).stem
        fname = write_chapter(output_path, n, chapter_title, content)
        chapter_files.append((chapter_title, fname))

    return title, author, chapter_files


# ── Output ───────────────────────────────────────────────────────────────────


def write_chapter(output_path: Path, n: int, title: str, content: str) -> str:
    fname = f"{n:02d}-{slugify(title)}.md"
    (output_path / "chapters" / fname).write_text(content, encoding="utf-8")
    return fname


def write_index(output_path: Path, title: str, author: str, chapter_files: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", ""]
    if author:
        lines += [f"**Author:** {author}", ""]
    lines += [f"**Chapters:** {len(chapter_files)}", "", "## Table of Contents", ""]
    for chapter_title, fname in chapter_files:
        lines.append(f"- [{chapter_title}](chapters/{fname})")
    (output_path / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── CLI ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDF/EPUB to per-chapter markdown files (raw-source layer of a book2wiki)")
    parser.add_argument("input", type=Path, help="Path to .pdf or .epub file")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Where to create the book's output folder (default: .)")
    parser.add_argument("--max-level", type=int, default=1, help="Max TOC depth for PDF (default: 1)")
    args = parser.parse_args()

    input_path: Path = args.input.expanduser().resolve()
    if not input_path.exists():
        print(f"error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in {".pdf", ".epub"}:
        print(f"error: unsupported file type: {ext} (use .pdf or .epub)", file=sys.stderr)
        sys.exit(1)

    output_dir: Path = args.output_dir.expanduser().resolve()

    if ext == ".pdf":
        doc = fitz.open(input_path)
        folder_title = pdf_title(doc, input_path)
        doc.close()
    else:
        book = epub.read_epub(str(input_path))
        folder_title = epub_title(book, input_path)

    output_path = output_dir / slugify(folder_title)
    (output_path / "chapters").mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_path}")

    if ext == ".pdf":
        title, author, chapter_files = extract_pdf(input_path, output_path, args.max_level)
    else:
        title, author, chapter_files = extract_epub(input_path, output_path)

    write_index(output_path, title, author, chapter_files)

    print(f"Done: {len(chapter_files)} chapter(s) → {output_path}/")
    # Emit the slug on the last line so a calling skill can capture the folder name.
    print(f"SLUG: {slugify(folder_title)}")


if __name__ == "__main__":
    main()
