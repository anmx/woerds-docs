#!/usr/bin/env python3
"""Checks around the Nextra build of the site; Nextra itself renders the pages.

  check     both user guides name the same app version
  postbuild adds what a static export cannot make to out/: the language choice at the root, the 404 page, redirects
            from earlier addresses, and the raw files of the language pack specification
  verify    fails when out/ lacks an address from tools/docs/urls.txt or a page links to something missing
"""

import html
import os
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
BASE_PATH = os.environ.get("NEXT_PUBLIC_BASE_PATH", "")

GUIDES = {
    ROOT / "content/en/user-guide.md": re.compile(r"This guide describes wörds (\d+\.\d+\.\d+)"),
    ROOT / "content/de/user-guide.md": re.compile(r"Dieses Handbuch beschreibt wörds (\d+\.\d+\.\d+)"),
}

SPEC_PAGES = ["language-pack-format", "issue-codes", "implementers-guide"]

# Earlier address -> page. The specification is English only, so the language switch leads from /en/spec to /de/spec.
REDIRECTS = {
    "de/benutzerhandbuch.html": "de/user-guide.html",
    "de/datenschutz.html": "de/privacy-policy.html",
    "spec/index.html": "en/spec.html",
    "de/spec.html": "en/spec.html",
    # GitHub Pages may answer /en, next to the folder en/, with a redirect to /en/.
    "en/index.html": "en.html",
    "de/index.html": "de.html",
    "en/spec/index.html": "en/spec.html",
    **{f"spec/v1/{page}.html": f"en/spec/v1/{page}.html" for page in SPEC_PAGES},
    **{f"de/spec/v1/{page}.html": f"en/spec/v1/{page}.html" for page in SPEC_PAGES},
}

SPEC_FILES = ["schema", "templates", "conformance"]

ROOT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>wörds</title>
<script>location.replace("{base}/" + (navigator.language.toLowerCase().startsWith("de") ? "de" : "en") + ".html")</script>
</head>
<body>
<h1>wörds</h1>
<ul>
<li><a href="{base}/en.html" hreflang="en">English</a></li>
<li><a href="{base}/de.html" hreflang="de" lang="de">Deutsch</a></li>
</ul>
</body>
</html>
"""

NOT_FOUND_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Page not found – wörds</title>
</head>
<body>
<h1>Page not found</h1>
<p>Only the guide of the latest version is kept. <span lang="de">Es gibt nur noch das Handbuch der aktuellen Version.</span></p>
<ul>
<li><a href="{base}/en/user-guide.html" hreflang="en">User guide</a></li>
<li><a href="{base}/de/user-guide.html" hreflang="de" lang="de">Benutzerhandbuch</a></li>
</ul>
</body>
</html>
"""


def redirect_page(target: str) -> str:
    """A page that moves on to target and keeps the anchor of the address it was opened with."""
    url = html.escape(f"{BASE_PATH}/{target}")
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace("{url}" + location.hash)</script>
<title>wörds</title>
</head>
<body><a href="{url}">{url}</a></body>
</html>
"""


def check() -> list[str]:
    """Returns the problems found in the guides."""
    versions = {}
    problems = []
    for path, sentence in GUIDES.items():
        match = sentence.search(path.read_text(encoding="utf-8"))
        if match:
            versions[path] = match.group(1)
        else:
            problems.append(f"{path.relative_to(ROOT)}: does not name the app version")
    if len(set(versions.values())) > 1:
        problems.append(f"the guides name different versions: {sorted(set(versions.values()))}")
    return problems


def postbuild(out: Path = OUT) -> None:
    (out / "index.html").write_text(ROOT_PAGE.format(base=BASE_PATH), encoding="utf-8")
    (out / "404.html").write_text(NOT_FOUND_PAGE.format(base=BASE_PATH), encoding="utf-8")
    for address, target in REDIRECTS.items():
        path = out / address
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(redirect_page(target), encoding="utf-8")
    for folder in SPEC_FILES:
        shutil.copytree(ROOT / "spec/v1" / folder, out / "spec/v1" / folder, dirs_exist_ok=True)


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "img" and values.get("src"):
            self.links.append(values["src"] or "")


def _resolve(out: Path, path: str) -> Path | None:
    """The file GitHub Pages answers the site path with, if any."""
    relative = path.strip("/")
    for candidate in (out / relative, out / f"{relative}.html", out / relative / "index.html"):
        if candidate.is_file():
            return candidate
    return None


def verify(out: Path = OUT, urls: Path = ROOT / "tools/docs/urls.txt") -> list[str]:
    """Returns every address from urls that is missing and every broken internal link or anchor."""
    problems = [
        f"missing address: {line}"
        for line in urls.read_text(encoding="utf-8").split()
        if _resolve(out, line) is None
    ]
    pages = {}
    for path in out.rglob("*.html"):
        page = _Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path] = page
    for path, page in pages.items():
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            target = path
            if parts.path:
                site_path = unquote(parts.path)
                if not site_path.startswith("/"):
                    continue
                site_path = site_path.removeprefix(BASE_PATH)
                target = _resolve(out, site_path)
                if target is None:
                    problems.append(f"{path.relative_to(out)}: broken link {link}")
                    continue
            fragment = unquote(parts.fragment)
            if fragment and target in pages and fragment not in pages[target].ids:
                problems.append(f"{path.relative_to(out)}: broken anchor {link}")
    return problems


def main() -> int:
    command = sys.argv[1] if len(sys.argv) == 2 else ""
    if command == "postbuild":
        postbuild()
        return 0
    if command not in ("check", "verify"):
        print(__doc__, file=sys.stderr)
        return 2
    problems = check() if command == "check" else verify()
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
