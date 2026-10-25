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

The user guide is versioned; the privacy policy is not (it applies to every version and carries its own date).
en/ and de/ hold the guide of the latest version, so its address never changes. Each earlier version is a frozen copy
in versions/<version>/ with the screenshots it showed (versions/<version>/images/), listed in versions.json. Guide
pages show which version they describe and link to the others; an earlier version's pages point to the latest one
and are kept out of search results. The version the guide names ("This guide describes wörds 0.10.0.") must match
versions.json, and index.html must link every earlier version.

Usage:

    python3 tools/docs/build-manual.py           # write the HTML files
    python3 tools/docs/build-manual.py --check   # exit with 1 when an HTML file is missing or out of date (CI)
    python3 tools/docs/build-manual.py --freeze 0.11.0  # before changing the guide for 0.11.0: copy the latest
                                                        # guide into versions/<latest>/ and make 0.11.0 the latest
"""
import html
import json
import os
import re
import shutil
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
    "en": {
        "home": "Manual", "other": "Deutsch", "skip": "Skip to content",
        "version": "Version {version}", "current": "Version {version} (latest)", "earlier": "Earlier versions:",
        "archived": "This guide describes wörds {version}, an earlier version.",
        "latest": "Guide for the latest version ({version})", "versions": "Versions",
    },
    "de": {
        "home": "Handbuch", "other": "English", "skip": "Zum Inhalt springen",
        "version": "Version {version}", "current": "Version {version} (aktuell)", "earlier": "Frühere Versionen:",
        "archived": "Dieses Handbuch beschreibt wörds {version}, eine frühere Version.",
        "latest": "Handbuch der aktuellen Version ({version})", "versions": "Versionen",
    },
}
# The versioned document per language, and the sentence in it that names the version it describes.
GUIDES = {"en": "en/user-guide.md", "de": "de/benutzerhandbuch.md"}
GUIDE_VERSION = {
    "en": re.compile(r"This guide describes wörds (\d+\.\d+\.\d+)\b"),
    "de": re.compile(r"Dieses Handbuch beschreibt wörds (\d+\.\d+\.\d+)\b"),
}
VERSIONS_FILE = "versions.json"
VERSIONS_DIRECTORY = "versions"
VERSION = re.compile(r"\d+\.\d+\.\d+")
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
    path = os.path.join(os.path.dirname(source), src)
    if not os.path.exists(path):
        raise ValueError(f"{os.path.relpath(source, ROOT)} shows {src}, which does not exist")
    width, height = png_size(path)
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


def read_versions():
    with open(os.path.join(ROOT, VERSIONS_FILE), encoding="utf-8") as f:
        versions = json.load(f)
    listed = [versions["latest"], *versions["archived"]]
    for version in listed:
        if not VERSION.fullmatch(version):
            raise ValueError(f"{VERSIONS_FILE}: '{version}' is not major.minor.patch")
    if len(set(listed)) != len(listed):
        raise ValueError(f"{VERSIONS_FILE} lists a version twice")
    return versions


def split_version(relative):
    """("0.9.0", "en/user-guide.md") for versions/0.9.0/en/user-guide.md; (None, relative) for the latest pages."""
    parts = relative.split("/")
    if parts[0] == VERSIONS_DIRECTORY:
        return parts[1], "/".join(parts[2:])
    return None, relative


def located(version, document):
    """The path from the root of a document (as in GUIDES) in a version; None stands for the latest."""
    return document if version is None else f"{VERSIONS_DIRECTORY}/{version}/{document}"


def version_bar(language, version, versions):
    """The note under the header of a guide page: the version it describes and links to the other versions."""
    labels, document = LABELS[language], GUIDES[language]
    here = located(version, document)

    def link(target_version, text):
        target = output_name(located(target_version, document))
        return f'<a href="{html.escape(href(target, here))}">{html.escape(text)}</a>'

    if version is None:
        lines = [f'<p class="version">{html.escape(labels["current"].format(version=versions["latest"]))}']
        if versions["archived"]:
            lines[0] += " · " + html.escape(labels["earlier"]) + " " + ", ".join(
                link(earlier, earlier) for earlier in versions["archived"])
        return [lines[0] + "</p>"]
    others = [earlier for earlier in versions["archived"] if earlier != version]
    note = (f'<p class="version archived" role="note">{html.escape(labels["archived"].format(version=version))} '
            + link(None, labels["latest"].format(version=versions["latest"])))
    if others:
        note += " · " + html.escape(labels["earlier"]) + " " + ", ".join(link(other, other) for other in others)
    return [note + "</p>"]


def href(target, page_path):
    """A relative link from the page at page_path to target, both relative to the root."""
    return os.path.relpath(target, os.path.dirname(page_path) or ".").replace(os.sep, "/")


def page(source, versions):
    relative = os.path.relpath(source, ROOT).replace(os.sep, "/")
    version, document = split_version(relative)
    language = document.split("/")[0]
    labels = LABELS[language]
    with open(source, encoding="utf-8") as f:
        markdown = f.read()
    guide = document == GUIDES[language]
    if guide:
        named = GUIDE_VERSION[language].search(markdown)
        expected = version or versions["latest"]
        if not named or named.group(1) != expected:
            raise ValueError(f"{relative} must say that it describes wörds {expected} (see {VERSIONS_FILE})")
    title, description, body = convert(markdown, source)
    if guide:
        body = version_bar(language, version, versions) + body
    other_document = COUNTERPARTS.get(document)
    other = other_document and located(version, other_document)
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light">',
        f'<meta name="theme-color" content="{THEME_COLOR}">',
    ]
    if description:
        head.append(f'<meta name="description" content="{html.escape(description)}">')
    if version:
        # Searches should find the guide of the latest version, not an earlier one.
        head.append('<meta name="robots" content="noindex">')
    head += [
        f"<title>{html.escape(re.sub(r'<[^>]+>', '', title))}</title>",
        f'<link rel="stylesheet" href="{href("manual.css", relative)}">',
    ]
    if other:
        for alternate in sorted((relative, other), key=lambda path: split_version(path)[1]):
            head.append(f'<link rel="alternate" hreflang="{split_version(alternate)[1].split("/")[0]}" '
                        f'href="{href(output_name(alternate), relative)}">')
    nav = [f'<a href="{href("index.html", relative)}">{labels["home"]}</a>']
    for target, label in PARTS[language]:
        # The guide links stay in the version of the page; the privacy policy has only one.
        target = located(version, target) if target == GUIDES[language] else target
        current = ' aria-current="page"' if target == relative else ""
        nav.append(f'<a href="{href(output_name(target), relative)}"{current}>{label}</a>')
    if other:
        other_language = split_version(other)[1].split("/")[0]
        nav.append(f'<a class="lang" href="{href(output_name(other), relative)}" hreflang="{other_language}" '
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


def sources(versions):
    """The Markdown pages: every page of the latest version, and the guides of the earlier ones."""
    for language in LANGUAGES:
        directory = os.path.join(ROOT, language)
        for name in sorted(os.listdir(directory)):
            if name.endswith(".md"):
                yield os.path.join(directory, name)
    for version in versions["archived"]:
        for language in LANGUAGES:
            source = os.path.join(ROOT, located(version, GUIDES[language]))
            if not os.path.exists(source):
                raise ValueError(f"{VERSIONS_FILE} lists {version}, but {os.path.relpath(source, ROOT)} is missing")
            yield source


def freeze(versions, new_version):
    """Copies the latest guides, with the images they show, into versions/<latest>/, lists that version as earlier
    and makes new_version the latest, also in the sentence of the guides that names it."""
    version = versions["latest"]
    if not VERSION.fullmatch(new_version) or new_version in (version, *versions["archived"]):
        raise ValueError(f"'{new_version}' is not a new major.minor.patch version")
    target = os.path.join(ROOT, VERSIONS_DIRECTORY, version)
    if os.path.exists(target):
        raise ValueError(f"{os.path.relpath(target, ROOT)} exists already")
    for language in LANGUAGES:
        source = os.path.join(ROOT, GUIDES[language])
        with open(source, encoding="utf-8") as f:
            markdown = f.read()
        images = {src for _, src in IMAGE.findall(markdown)}
        copy = os.path.join(target, GUIDES[language])
        os.makedirs(os.path.dirname(copy), exist_ok=True)
        shutil.copyfile(source, copy)
        for src in images:
            # The copy keeps the layout of the root, so the relative image paths stay valid.
            image = os.path.normpath(os.path.join(os.path.dirname(source), src))
            image_copy = os.path.join(target, os.path.relpath(image, ROOT))
            os.makedirs(os.path.dirname(image_copy), exist_ok=True)
            shutil.copyfile(image, image_copy)
        named = GUIDE_VERSION[language].search(markdown)
        if not named:
            raise ValueError(f"{GUIDES[language]} does not say which version it describes")
        with open(source, "w", encoding="utf-8") as f:
            f.write(markdown[:named.start(1)] + new_version + markdown[named.end(1):])
    versions["archived"].insert(0, version)
    versions["latest"] = new_version
    with open(os.path.join(ROOT, VERSIONS_FILE), "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)
        f.write("\n")
    print(f"Froze {version} in {os.path.relpath(target, ROOT)}; the guides now describe {new_version}. Link "
          f"{version} in index.html and README.md, then run this tool again.")


def unlisted(versions):
    """Earlier versions that index.html does not link to."""
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        index = f.read()
    return [version for version in versions["archived"]
            if any(f'href="{output_name(located(version, GUIDES[language]))}"' not in index for language in LANGUAGES)]


def main():
    check = "--check" in sys.argv[1:]
    versions = read_versions()
    if "--freeze" in sys.argv[1:]:
        arguments = sys.argv[1:]
        position = arguments.index("--freeze") + 1
        if position >= len(arguments):
            raise ValueError("--freeze needs the new version, for example --freeze 0.11.0")
        freeze(versions, arguments[position])
        return
    stale = []
    for source in sources(versions):
        target = output_name(source)
        content = page(source, versions)
        current = open(target, encoding="utf-8").read() if os.path.exists(target) else None
        if current != content:
            stale.append(os.path.relpath(target, ROOT))
            if not check:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
    missing = unlisted(versions)
    if missing:
        print("index.html does not link the guides of " + ", ".join(missing), file=sys.stderr)
    if check and stale:
        print("Out of date: " + ", ".join(stale) + "\nRun: python3 tools/docs/build-manual.py", file=sys.stderr)
    if missing or (check and stale):
        sys.exit(1)
    print(("Up to date" if check else "Written: " + (", ".join(stale) or "nothing changed")))


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
