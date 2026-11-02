import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("site_tool", Path(__file__).with_name("site.py"))
assert spec and spec.loader
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class CheckTest(unittest.TestCase):
    def guides(self, en: str, de: str) -> None:
        folder = Path(self.tmp.name)
        (folder / "en.md").write_text(en, encoding="utf-8")
        (folder / "de.md").write_text(de, encoding="utf-8")
        self.original = site.GUIDES
        patterns = list(site.GUIDES.values())
        site.GUIDES = {folder / "en.md": patterns[0], folder / "de.md": patterns[1]}
        site.ROOT, self.root = folder, site.ROOT
        self.addCleanup(self.restore)

    def restore(self) -> None:
        site.GUIDES, site.ROOT = self.original, self.root

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_same_version_passes(self) -> None:
        self.guides("This guide describes wörds 1.2.3.", "Dieses Handbuch beschreibt wörds 1.2.3.")
        self.assertEqual(site.check(), [])

    def test_different_versions_fail(self) -> None:
        self.guides("This guide describes wörds 1.2.3.", "Dieses Handbuch beschreibt wörds 1.2.4.")
        self.assertIn("different versions", site.check()[0])

    def test_missing_sentence_fails(self) -> None:
        self.guides("Nothing here.", "Dieses Handbuch beschreibt wörds 1.2.3.")
        self.assertIn("does not name", site.check()[0])


class RedirectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(setattr, site, "BASE_PATH", site.BASE_PATH)
        site.BASE_PATH = ""

    def test_keeps_the_anchor(self) -> None:
        page = site.redirect_page("de/user-guide.html")
        self.assertIn('location.replace("/de/user-guide.html" + location.hash)', page)
        self.assertIn('rel="canonical" href="/de/user-guide.html"', page)

    def test_every_redirect_leads_to_a_page_that_is_not_itself_a_redirect(self) -> None:
        for target in site.REDIRECTS.values():
            self.assertNotIn(target, site.REDIRECTS)


class VerifyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(setattr, site, "BASE_PATH", site.BASE_PATH)
        site.BASE_PATH = ""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name)
        self.urls = self.out / "urls.txt"
        self.urls.write_text("a.html\n", encoding="utf-8")

    def write(self, name: str, body: str) -> None:
        (self.out / name).write_text(body, encoding="utf-8")

    def test_good_links_pass(self) -> None:
        self.write("a.html", '<a href="/b#läufe">x</a><a href="https://example.com/y">y</a><a href="#top">z</a><i id="top"></i>')
        self.write("b.html", '<h2 id="läufe">b</h2>')
        self.assertEqual(site.verify(self.out, self.urls), [])

    def test_missing_address_fails(self) -> None:
        self.write("b.html", "")
        self.assertEqual(site.verify(self.out, self.urls), ["missing address: a.html"])

    def test_broken_link_and_anchor_fail(self) -> None:
        self.write("a.html", '<a href="/gone">x</a><a href="/b#gone">y</a>')
        self.write("b.html", "")
        problems = site.verify(self.out, self.urls)
        self.assertEqual(len(problems), 2)
        self.assertIn("broken link", problems[0])
        self.assertIn("broken anchor", problems[1])


if __name__ == "__main__":
    unittest.main()
