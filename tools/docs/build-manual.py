#!/usr/bin/env python3
"""Builds the HTML pages of the wörds manual from their Markdown sources.

Every en/*.md and de/*.md gets an .html file next to it, styled by manual.css. index.html is written by hand, because
it mixes both languages; keep it in step with README.md. The converter covers the Markdown the pages use: headings,
paragraphs, lists, tables, fenced code, images, links, autolinks and bare URLs, bold, italic and inline code. On top
of that:

- Paragraphs made only of images become a row of screenshots with their alt text as caption; width and height come
  from the PNG header, so the layout does not shift while they load.
- A list made only of links to headings on the same page becomes the page's table of contents.
- A table cell that is entirely bold in the first column becomes the row's header cell.
- Dates (YYYY-MM-DD) become <time> elements. Addresses written as "name _at_ host _dot_ tld" become an address with a
  hidden decoy part, so that harvesters copying the text get a wrong address.

Usage:

    python3 tools/docs/build-manual.py           # write the HTML files
    python3 tools/docs/build-manual.py --check   # exit with 1 when an HTML file is missing or out of date (CI)
"""
import html
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGUAGES = ("en", "de")

# The same document in the other language, for the language switch in the header and the hreflang links.
COUNTERPARTS = {
    "en/user-guide.md": "de/benutzerhandbuch.md",
    "en/privacy-policy.md": "de/datenschutz.md",
}
COUNTERPARTS.update({de: en for en, de in COUNTERPARTS.items()})

LABELS = {
    "en": {"home": "Manual", "other": "Deutsch", "skip": "Skip to content"},
    "de": {"home": "Handbuch", "other": "English", "skip": "Zum Inhalt springen"},
}
# The header lists the parts of the site, in this order.
PARTS = {
    "en": (("en/user-guide.md", "User guide"), ("en/privacy-policy.md", "Privacy policy")),
    "de": (("de/benutzerhandbuch.md", "Benutzerhandbuch"), ("de/datenschutz.md", "Datenschutz")),
}
# --tint in manual.css: the browser's UI color on mobile.
THEME_COLOR = "#f5f9fd"
# Search results show about 160 characters of the description.
DESCRIPTION_LENGTH = 160
# Shorter paragraphs (dates, the provider line) do not describe the page.
DESCRIPTION_MIN_LENGTH = 120

IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# <https://…> and, as on GitHub, bare URLs; not the target of a [text](url) link.
AUTOLINK = re.compile(r"<(https?://[^>\s]+)>|(?<!\]\()\b(https?://[^\s<>()]+[^\s<>().,;:])")
EMAIL = re.compile(r"([\w.+-]+) _at_ ([\w-]+) _dot_ ([\w.-]+)")
DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
LIST_ITEM = re.compile(r"(- |\d+\. )")
TOC_ITEM = re.compile(r"- \[[^\]]+\]\(#[^)\s]+\)$")


def slug(text):
    """GitHub's heading anchors: lower case, punctuation removed, spaces as hyphens."""
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def output_name(source):
    return source[:-3] + ".html"


def link_target(target, source):
    """Links to Markdown files of the site point to their HTML version; everything else stays as it is."""
    path, _, anchor = target.partition("#")
    if path.endswith(".md") and not re.match(r"^[a-z]+:", path):
        resolved = os.path.normpath(os.path.join(os.path.dirname(source), path))
        if resolved.startswith(ROOT + os.sep) and os.path.exists(resolved):
            path = os.path.relpath(output_name(resolved), os.path.dirname(source))
    return path + ("#" + anchor if anchor else "")


def inline(text, source):
    kept = []

    def keep(markup):
        kept.append(markup)
        return f"\x00{len(kept) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: keep("<code>" + html.escape(m.group(1)) + "</code>"), text)
    def autolink(match):
        url = html.escape(match.group(1) or match.group(2))
        return keep(f'<a href="{url}">{url}</a>')

    text = AUTOLINK.sub(autolink, text)
    text = EMAIL.sub(
        lambda m: keep(f'<span class="email">{html.escape(m.group(1))}@<span class="decoy">no.spam.</span>'
                       f'{html.escape(m.group(2))}.{html.escape(m.group(3))}</span>'),
        text,
    )
    text = html.escape(text, quote=False)
    text = LINK.sub(lambda m: f'<a href="{html.escape(link_target(m.group(2), source))}">{m.group(1)}</a>', text)
    text = DATE.sub(r'<time datetime="\1">\1</time>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], text)


def png_size(path):
    with open(path, "rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG file")
    return struct.unpack(">II", header[16:24])


def figure(alt, src, source):
    width, height = png_size(os.path.join(os.path.dirname(source), src))
    wide = "/tablet/" in src
    return [
        f'<figure class="{"wide" if wide else "shot"}">',
        f'  <img src="{html.escape(src)}" alt="{html.escape(alt)}" width="{width}" height="{height}" loading="lazy" '
        'decoding="async">',
        f"  <figcaption>{html.escape(alt)}</figcaption>",
        "</figure>",
    ]


def table(rows, source):
    def cells(row):
        return [cell.strip() for cell in row.strip().strip("|").split("|")]

    def cell(text, first):
        bold = re.fullmatch(r"\*\*(.+)\*\*", text)
        if first and bold:
            return f'<th scope="row">{inline(bold.group(1), source)}</th>'
        return f"<td>{inline(text, source)}</td>"

    head, body = cells(rows[0]), [cells(row) for row in rows[2:]]
    out = ['<div class="table">', "  <table>"]
    if any(head):
        out += ["    <thead>", "      <tr>" + "".join(f'<th scope="col">{inline(c, source)}</th>' for c in head)
                + "</tr>", "    </thead>"]
    out.append("    <tbody>")
    for row in body:
        out.append("      <tr>" + "".join(cell(c, i == 0) for i, c in enumerate(row)) + "</tr>")
    out += ["    </tbody>", "  </table>", "</div>"]
    return out


def indented(lines, depth=1):
    return ["  " * depth + line for line in lines]


def convert(markdown, source):
    """Returns the title (first heading), the description and the HTML lines of the main content."""
    lines = markdown.split("\n")
    out, title, description, heading, i = [], None, None, None, 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            end = next(j for j in range(i + 1, len(lines)) if lines[j].startswith("```"))
            # The content of <pre> keeps its own indentation, so it goes out as one entry.
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:end])) + "</code></pre>")
            i = end + 1
        elif re.match(r"#{1,4} ", line):
            level = len(line) - len(line.lstrip("#"))
            text = inline(line[level + 1:].strip(), source)
            title = title or text
            heading = slug(text)
            out.append(f'<h{level} id="{heading}">{text}</h{level}>')
            i += 1
            continue
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out += table(rows, source)
        elif LIST_ITEM.match(line):
            ordered = not line.startswith("- ")
            items = []
            while i < len(lines) and (LIST_ITEM.match(lines[i]) or lines[i].startswith("  ")):
                if LIST_ITEM.match(lines[i]):
                    items.append(LIST_ITEM.sub("", lines[i], count=1))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            tag = "ol" if ordered else "ul"
            markup = [f"<{tag}>"] + [f"  <li>{inline(item, source)}</li>" for item in items] + [f"</{tag}>"]
            toc = heading and out[-1].startswith("<h") and all(TOC_ITEM.match("- " + item) for item in items)
            out += [f'<nav aria-labelledby="{heading}">'] + indented(markup) + ["</nav>"] if toc else markup
        else:
            block = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,4} |```|\||- |\d+\. )", lines[i]):
                block.append(lines[i].strip())
                i += 1
            text = " ".join(block)
            images = IMAGE.findall(text)
            if images and not IMAGE.sub("", text).strip():
                out += ['<div class="figures">'] + indented([l for a, s in images for l in figure(a, s, source)]) + [
                    "</div>"]
            else:
                markup = inline(text, source)
                plain = html.unescape(re.sub(r"<[^>]+>", "", markup))
                if description is None and len(plain) >= DESCRIPTION_MIN_LENGTH:
                    description = shorten(plain)
                out.append(f"<p>{markup}</p>")
        heading = None
    return title or "wörds", description, out


def shorten(text):
    if len(text) <= DESCRIPTION_LENGTH:
        return text
    return text[:DESCRIPTION_LENGTH - 1].rsplit(" ", 1)[0] + "…"


def page(source):
    relative = os.path.relpath(source, ROOT).replace(os.sep, "/")
    language = relative.split("/")[0]
    labels = LABELS[language]
    with open(source, encoding="utf-8") as f:
        title, description, body = convert(f.read(), source)
    other = COUNTERPARTS.get(relative)
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light">',
        f'<meta name="theme-color" content="{THEME_COLOR}">',
    ]
    if description:
        head.append(f'<meta name="description" content="{html.escape(description)}">')
    head += [
        f"<title>{html.escape(re.sub(r'<[^>]+>', '', title))}</title>",
        '<link rel="stylesheet" href="../manual.css">',
    ]
    if other:
        for version in sorted((relative, other)):
            head.append(f'<link rel="alternate" hreflang="{version.split("/")[0]}" href="../{output_name(version)}">')
    nav = [f'<a href="../index.html">{labels["home"]}</a>']
    for target, label in PARTS[language]:
        current = ' aria-current="page"' if target == relative else ""
        nav.append(f'<a href="../{output_name(target)}"{current}>{label}</a>')
    if other:
        other_language = other.split("/")[0]
        nav.append(f'<a class="lang" href="../{output_name(other)}" hreflang="{other_language}" '
                   f'lang="{other_language}">{labels["other"]}</a>')
    lines = (
        ["<!doctype html>", f'<html lang="{language}">', "<head>"]
        + indented(head)
        + ["</head>", "<body>"]
        + indented(
            ["<!-- Generated from the Markdown next to this file by tools/docs/build-manual.py; edit the Markdown. -->",
             f'<a class="skip-link" href="#main">{labels["skip"]}</a>',
             "<header>", f'  <nav aria-label="{labels["home"]}">']
            + indented(nav, 2)
            + ["  </nav>", "</header>", '<main id="main">']
            + indented(body)
            + ["</main>"]
        )
        + ["</body>", "</html>"]
    )
    return "\n".join(lines) + "\n"


def main():
    check = "--check" in sys.argv[1:]
    stale = []
    for language in LANGUAGES:
        directory = os.path.join(ROOT, language)
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".md"):
                continue
            source = os.path.join(directory, name)
            target = output_name(source)
            content = page(source)
            current = open(target, encoding="utf-8").read() if os.path.exists(target) else None
            if current != content:
                stale.append(os.path.relpath(target, ROOT))
                if not check:
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(content)
    if check and stale:
        print("Out of date: " + ", ".join(stale) + "\nRun: python3 tools/docs/build-manual.py", file=sys.stderr)
        sys.exit(1)
    print(("Up to date" if check else "Written: " + (", ".join(stale) or "nothing changed")))


if __name__ == "__main__":
    main()
