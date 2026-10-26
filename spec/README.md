# wörds language pack specification

wörds learns from language packs: words, verb forms and lections in a `.linguapack` file. This specification describes
that format completely, so that packs can be made and edited outside the app, in a web app, a desktop editor or a
converter from other formats.

## Contents

| Document | What it is for |
| --- | --- |
| [Language pack format, version 1](v1/language-pack-format.md) | The specification: archive, files, manifest, content types, rules, updates, editable packs, repository index |
| [Issue codes](v1/issue-codes.md) | Every validation code with its severity, meaning and fix |
| [Implementers' guide](v1/implementers-guide.md) | Advice for building an editor: data model, ids, validation, deterministic archives, publishing, testing |
| [`v1/schema/pack.schema.json`](v1/schema/pack.schema.json) | JSON Schema (draft 2020-12) of `pack.json` and of included content files |
| [`v1/schema/index.schema.json`](v1/schema/index.schema.json) | JSON Schema of the repository index `lingua-index.json` |
| [`v1/templates/`](v1/templates/) | Example packs to start from, as folders and as archives, and an example index |
| [`v1/conformance/`](v1/conformance/) | Small packs that each test one rule, with the codes a reader reports in [`cases.json`](v1/conformance/cases.json) |

Start with section 2 of the specification for an overview, then copy a template.

## Versions

The **format version** is the number packs carry in `formatVersion`. Version 1 is the only one so far, and the folder
`v1/` describes it. A later format version gets a folder of its own, and `v1/` stays as it is for the packs written
in version 1.

The specification itself has **revisions**, listed at its end. A revision makes the text clearer or more complete; it
never changes what a valid version 1 pack is, unless the app changed, in which case the revision says so.

The specification describes what the app actually does. A test in the app's repository checks this repository: the
schema copy against the generated schema, the templates and conformance cases against the app's validator, and the
issue-code catalogue against the app's codes.

## Building

The archives of the templates and of the archive-level conformance cases, and the template index, are generated from
the folders next to them:

```text
python3 tools/spec/build-spec.py           # write the archives and the index
python3 tools/spec/build-spec.py --check   # check that they are up to date (CI)
```

The HTML pages are built with the rest of the site: `python3 tools/docs/build-manual.py`.

## Licenses

- The specification text (the Markdown and HTML pages in `spec/`) is licensed under the
  [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)
  (CC BY 4.0). See [LICENSE](LICENSE).
- The schemas, the templates (including their pictures) and the conformance cases are dedicated to the public domain
  under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): copy them into your own software without
  conditions. See [`v1/schema/LICENSE`](v1/schema/LICENSE).

Questions and corrections are welcome as issues in [anmx/woerds-docs](https://github.com/anmx/woerds-docs/issues).
