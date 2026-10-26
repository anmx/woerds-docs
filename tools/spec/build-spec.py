#!/usr/bin/env python3
"""Builds the archives and the repository index of the language pack specification, and checks them.

The pack directories under spec/v1/templates/ and spec/v1/conformance/ are the sources. This tool writes:

- spec/v1/templates/<name>.linguapack for every template directory, and spec/v1/templates/lingua-index.json, the
  repository index that lists them (with the SHA-256 and size of each archive).
- spec/v1/conformance/invalid/archive-*.linguapack, archives that break the rules of the zip container itself. They
  cannot be kept as directories, so they are generated here.

Archives are written the way the app exports packs: entries in path order, all dated 1980-01-01 00:00, JSON deflated
and every other file stored. The deflated bytes depend on the zlib version, so an archive is only rewritten when its
entries differ from its directory; an unchanged archive keeps its bytes and its checksum in the index.

--check (run by CI) also makes sure that every JSON file parses (except the deliberately broken ones in conformance),
that spec/v1/conformance/cases.json lists every case exactly once and only cases that exist, and that the schema copy
is valid JSON. Whether the cases give the codes they promise is checked against the app's validator in the app
repository (SpecDriftTest), which reads this repository.

Usage:

    python3 tools/spec/build-spec.py           # write the archives and the index
    python3 tools/spec/build-spec.py --check   # exit with 1 when something is missing or out of date (CI)
"""
import hashlib
import io
import json
import os
import sys
import warnings
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(ROOT, "spec", "v1")
TEMPLATES = os.path.join(SPEC, "templates")
CONFORMANCE = os.path.join(SPEC, "conformance")
CASES = os.path.join(CONFORMANCE, "cases.json")
INDEX = os.path.join(TEMPLATES, "lingua-index.json")

ZIP_DATE = (1980, 1, 1, 0, 0, 0)
DEFLATED_EXTENSIONS = {"json"}
INDEX_VERSION = 1
STAGES = ("archive", "read", "import")


def relative(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def entry(name, data, deflate=None):
    """A zip entry as the app writes it: fixed date, no extra fields, JSON deflated."""
    info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
    info.create_system = 0
    info.external_attr = 0
    if deflate is None:
        deflate = name.rsplit(".", 1)[-1].lower() in DEFLATED_EXTENSIONS
    info.compress_type = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
    return info, data


def archive(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file, warnings.catch_warnings():
        # One conformance case has a duplicate entry on purpose.
        warnings.simplefilter("ignore", UserWarning)
        for info, data in entries:
            zip_file.writestr(info, data, compresslevel=9)
    return buffer.getvalue()


def directory_files(directory):
    """Every file of a pack directory as {path: bytes}, with '/' separators."""
    files = {}
    for base, folders, names in os.walk(directory):
        folders.sort()
        for name in names:
            if name == ".DS_Store":
                continue
            path = os.path.join(base, name)
            files[os.path.relpath(path, directory).replace(os.sep, "/")] = open(path, "rb").read()
    return files


def archive_entries(data):
    """The entries of an archive as a list of (name, bytes, compress type, date), or None when it is no zip."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zip_file:
            return [(i.filename, zip_file.read(i), i.compress_type, i.date_time) for i in zip_file.infolist()]
    except (zipfile.BadZipFile, EOFError, KeyError):
        return None


def same_archive(expected, current):
    """Equal bytes, or the same entries in the same order (deflate output differs between zlib versions). A case that
    is broken on purpose only has to stay unreadable: other Python versions may write its headers differently."""
    if current is None:
        return False
    if expected == current:
        return True
    expected_entries, current_entries = archive_entries(expected), archive_entries(current)
    return expected_entries == current_entries


def template_archives():
    """{archive path: bytes} for every template directory."""
    archives = {}
    for name in sorted(os.listdir(TEMPLATES)):
        directory = os.path.join(TEMPLATES, name)
        if os.path.isdir(directory) and os.path.exists(os.path.join(directory, "pack.json")):
            files = directory_files(directory)
            archives[directory + ".linguapack"] = archive([entry(path, files[path]) for path in sorted(files)])
    return archives


def conformance_archives():
    """{archive path: bytes} for the cases that break the zip container. Small, valid packs otherwise."""
    pack = json.dumps({
        "formatVersion": 1, "id": "org.example.conformance", "version": "1.0.0", "title": "Conformance case",
        "license": "CC0-1.0", "sourceLanguage": "de", "targetLanguage": "it",
        "sections": [{"id": "s1", "title": "Lektion 1"}],
        "content": [{"type": "vocabulary", "entries": [
            {"id": "casa", "term": "la casa", "translation": "das Haus", "sectionIds": ["s1"]}]}],
    }, indent=2, ensure_ascii=False).encode() + b"\n"
    valid = archive([entry("pack.json", pack, deflate=False)])
    invalid = os.path.join(CONFORMANCE, "invalid")
    cases = {
        "archive-valid-stored": valid,
        "archive-unsafe-path": archive([entry("../outside.json", b"{}\n", deflate=False),
                                        entry("pack.json", pack, deflate=False)]),
        "archive-absolute-path": archive([entry("/pack.json", pack, deflate=False)]),
        "archive-duplicate-entry": archive([entry("pack.json", pack, deflate=False),
                                            entry("pack.json", pack, deflate=False)]),
        "archive-empty": archive([]),
        "archive-not-a-zip": b"This is a text file, not a zip archive.\n",
        "archive-truncated": valid[:len(valid) // 2],
        # 2 MiB of spaces deflate to a few KiB: far above the allowed ratio of 100.
        "archive-compression-ratio": archive([entry("content/padding.json", b" " * (2 * 1024 * 1024), deflate=True),
                                              entry("pack.json", pack, deflate=False)]),
    }
    folder = {"archive-valid-stored": os.path.join(CONFORMANCE, "valid")}
    return {os.path.join(folder.get(name, invalid), name + ".linguapack"): data for name, data in cases.items()}


def pack_summary(directory):
    """What the index says about a pack, read from its directory."""
    with open(os.path.join(directory, "pack.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    blocks = list(manifest.get("content", []))
    for include in manifest.get("includes", []):
        with open(os.path.join(directory, include), encoding="utf-8") as f:
            blocks.append(json.load(f))
    return manifest, sorted({block["type"] for block in blocks})


def index(archives):
    """The repository index for the template archives, as the app's index generator writes it."""
    packs = []
    for path, data in archives.items():
        manifest, types = pack_summary(path[:-len(".linguapack")])
        pack = {
            "id": manifest["id"],
            "path": os.path.relpath(path, TEMPLATES).replace(os.sep, "/"),
            "version": manifest["version"],
            "formatVersion": manifest["formatVersion"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "sourceLanguage": manifest["sourceLanguage"],
            "targetLanguage": manifest["targetLanguage"],
            "contentTypes": types,
            "title": manifest["title"],
            "sizeBytes": len(data),
        }
        if manifest.get("description"):
            pack["description"] = manifest["description"]
        packs.append(pack)
    packs.sort(key=lambda pack: pack["id"])
    return json.dumps({"indexVersion": INDEX_VERSION, "packs": packs}, indent=4, ensure_ascii=False) + "\n"


def case_paths():
    """Every case on disk: the directories and archives directly in conformance/valid and conformance/invalid."""
    paths = set()
    for kind in ("valid", "invalid"):
        folder = os.path.join(CONFORMANCE, kind)
        for name in os.listdir(folder):
            if name != ".DS_Store":
                paths.add(f"{kind}/{name}")
    return paths


def check_cases():
    problems = []
    with open(CASES, encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    listed = [case["path"] for case in cases]
    for path in sorted({path for path in listed if listed.count(path) > 1}):
        problems.append(f"cases.json lists {path} more than once")
    for path in sorted(case_paths() - set(listed)):
        problems.append(f"cases.json does not list {path}")
    for case in cases:
        path = case["path"]
        if path not in case_paths():
            problems.append(f"cases.json lists {path}, which does not exist")
        if case.get("stage") not in STAGES:
            problems.append(f"{path}: stage must be one of {', '.join(STAGES)}")
        if case["valid"] != (not case["errors"]):
            problems.append(f"{path}: a case is valid exactly when it expects no errors")
        if path.startswith("valid/") != case["valid"]:
            problems.append(f"{path}: valid cases belong in valid/, invalid ones in invalid/")
    return problems


def check_json():
    """Every JSON file parses, except the content of invalid conformance cases (some are broken on purpose)."""
    problems = []
    skip = os.path.join(CONFORMANCE, "invalid") + os.sep
    for base, _, names in os.walk(os.path.join(ROOT, "spec")):
        for name in names:
            path = os.path.join(base, name)
            if not name.endswith(".json") or path.startswith(skip):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    json.load(f)
            except (ValueError, UnicodeDecodeError) as error:
                problems.append(f"{relative(path)}: {error}")
    return problems


def main():
    check = "--check" in sys.argv[1:]
    stale = []
    archives = template_archives()
    for path, data in {**archives, **conformance_archives()}.items():
        current = open(path, "rb").read() if os.path.exists(path) else None
        if not same_archive(data, current):
            stale.append(relative(path))
            if not check:
                with open(path, "wb") as f:
                    f.write(data)
    # The index describes the archives as they are on disk, which may be older (but equal) bytes.
    on_disk = {path: open(path, "rb").read() if os.path.exists(path) else data for path, data in archives.items()}
    content = index(on_disk)
    current = open(INDEX, encoding="utf-8").read() if os.path.exists(INDEX) else None
    if current != content:
        stale.append(relative(INDEX))
        if not check:
            with open(INDEX, "w", encoding="utf-8") as f:
                f.write(content)
    problems = check_json() + check_cases()
    for problem in problems:
        print(problem, file=sys.stderr)
    if check and stale:
        print("Out of date: " + ", ".join(stale) + "\nRun: python3 tools/spec/build-spec.py", file=sys.stderr)
    if problems or (check and stale):
        sys.exit(1)
    print("Up to date" if check else "Written: " + (", ".join(stale) or "nothing changed"))


if __name__ == "__main__":
    main()
