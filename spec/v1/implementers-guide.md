# Implementers' guide to wörds language packs

Advice for building tools that create and edit wörds language packs: web apps, desktop editors, converters from
spreadsheets or other flashcard formats. This guide is informative. Where it repeats a rule, the
[format specification](language-pack-format.md) is the authority.

## Contents

- [What an editor does](#what-an-editor-does)
- [Data model](#data-model)
- [Opening packs](#opening-packs)
- [Editing](#editing)
- [Validating](#validating)
- [Writing archives](#writing-archives)
- [Publishing in a repository](#publishing-in-a-repository)
- [Testing with the conformance cases](#testing-with-the-conformance-cases)
- [Checklist before a release](#checklist-before-a-release)

## What an editor does

1. **Open** a pack: a `.linguapack` file, a pack folder, or a new empty pack.
2. **Edit** it in a model that holds exactly what the format can express.
3. **Validate** while the user types, with the same rules and codes as the app.
4. **Save** it as a pack folder or as a deterministic `.linguapack` archive, with a higher version.
5. Optionally **publish** it in a repository with an index, or hand it to the app as an editable pack.

## Data model

Format version 1 rejects unknown fields, so a model with exactly the fields of the specification loses nothing on a
round trip. Keep in it:

- the manifest fields, including `$schema` if the file had one;
- the sections in their list order, with `order` and `parentId` as written;
- the content blocks in order, and for each block whether it was inline or in which included file, so that saving
  keeps the file layout the author chose;
- blocks of types your editor does not know, as raw JSON, written back unchanged;
- the media files by their paths, and documentation files (`LICENSE`, `NOTICE`, `README.md`) as they are.

Ids are the identity of everything that carries learning progress (section 12 of the specification). Store them as
fields of their own that the user does not edit by accident, not as something derived from a word's text on every
save.

## Opening packs

Users open files from anywhere, so an editor should be as careful as a reader:

- Extract archives into memory or a fresh folder, refuse unsafe entry names, duplicates and zip bombs, and count the
  bytes yourself (section 3 of the specification).
- Accept both stored and deflated entries, and data descriptors on deflated entries.
- Read JSON strictly and report problems with their issue codes, but still show what could be read, so the user can
  repair a broken pack.
- Normalize all text to NFC when you load it. Readers do the same, so a pack that differs only in normalization means
  the same to them.

## Editing

### Ids

- Generate ids for new items once, when they are created, and never change them afterwards. Random ids are the
  safest: the app uses `w` or `l` followed by 12 characters from `a`–`z` and `2`–`7` (60 random bits). Readable ids
  such as `casa` are fine for hand-made packs, as long as they stay the same when the word is corrected.
- Never reuse the id of a deleted item for a different word: if the learner still has progress for it, the new word
  inherits it.
- Validate ids against `^[a-z0-9]+([._-][a-z0-9]+)*$` and at most 100 characters. Ids contain neither `|` nor `/`.
- Choose the pack id once, when the pack is created, with a prefix the author controls, and do not offer to change it
  for published packs.

### Versions

- Raise the version on every save that is meant to be shared, at least the patch number. A pack whose version did
  not change and whose content did replaces the installed one, which is confusing; one with a lower version is
  refused.
- Offer the minor or major number as a choice when items are added or ids change.

### Text

- Count lengths in UTF-16 code units, as the format does: `string.length` in JavaScript, `string.utf16.count` in
  Swift, `string.Length` in C#. Count after NFC normalization.
- Refuse control characters other than tab and line feed. Convert pasted line breaks (`\r\n`, `\r`) to `\n`.
- Trim white space at both ends of every field, and leave optional fields out instead of writing empty strings.
- Show which fields appear where on the card, so authors know what to write (sections 9 and 10 of the
  specification). Hint at the conventions typed answers understand: `,`, `;` and ` / ` separate alternatives, a slash
  inside a word offers a choice, parentheses hold notes.
- Write nouns with their article (`la casa`, `l'acqua`) and fill `partOfSpeech` and `gender`, so the article drill can
  use them.

### Sections

- Prevent cycles when the user moves a section under another one.
- Write an explicit `order` for every section, numbered among its siblings.
- Warn about items without a section, unless the pack is meant to be edited in the app (`user.` id).

### Pictures and recordings

- Convert pictures to PNG or WebP, at most 1,024 pixels on the longer side and at most 1 MiB, without animation and
  without metadata (camera data, location, text chunks).
- Ask for a description of each picture in the source language; screen readers read it.
- Give media files stable, unique names, such as a random id or a content hash, and keep a file's name when it is
  re-saved unchanged.
- Remove media that no entry references any more when you save.

### Editable packs for the app

To hand a pack to the app for further editing, give it an id starting with `user.` and follow section 13 of the
specification: one vocabulary block, at most one section per entry, titles of at most 100 characters, a description
for every picture, and no audio or speech texts (the app drops them). The learner imports the file in the app, and it
becomes an editable pack.

## Validating

Validate in two layers.

**The JSON Schema** ([`schema/pack.schema.json`](schema/pack.schema.json), draft 2020-12) checks the structure:
fields, types, required fields, patterns and allowed values. Use a validator that supports draft 2020-12 and
`if`/`then`, such as Ajv (with its 2020 build) in JavaScript, JsonSchema.Net in .NET, `jsonschema` in Python or
networknt's validator on the JVM. For an included file, validate against `#/$defs/contentBlock`. The schemas are
published at `https://anmx.github.io/woerds-docs/spec/v1/schema/`, and the templates name that address in `$schema`,
so text editors such as Visual Studio Code check packs while they are edited.

**The rules the schema cannot express**, implemented in your code with the codes from the
[catalogue](issue-codes.md):

| Rule | Codes |
| --- | --- |
| NFC normalization, then length and control characters of every string | `syntax.string-too-long`, `syntax.control-character` |
| Blank titles and texts | `manifest.blank-title`, `sections.blank-title`, `vocabulary.blank`, `conjugation.blank` |
| Primary languages differ; speech locale matches the target language | `manifest.same-languages`, `manifest.tts-language-mismatch` |
| Section ids unique, parents exist, no cycles | `sections.duplicate-id`, `sections.unknown-parent`, `sections.cycle` |
| Item ids unique within a block and across blocks of a type | `vocabulary.duplicate-entry`, `conjugation.duplicate-verb`, `conjugation.duplicate-id`, `content.duplicate-item` |
| References to sections, tenses and persons exist | `vocabulary.unknown-section`, `conjugation.unknown-section`, `conjugation.unknown-tense`, `conjugation.unknown-person` |
| One conjugation per tense, one form per person | `conjugation.duplicate-tense`, `conjugation.duplicate-form` |
| Warnings that help authors | `vocabulary.duplicate-term`, `vocabulary.no-section`, `vocabulary.no-image-description`, `vocabulary.description-without-image`, `conjugation.no-section`, `conjugation.generated-prompt`, `conjugation.incomplete-grid`, `manifest.missing-license` |
| Files: allowed names, paths, existence, kind, signature, size, picture headers | `files.*` |
| Archives | `archive.*` |

Show issues next to the field their path points to, and use the codes, not the English messages, for your own texts.
Treat warnings as things to fix before publishing: the app's own packs have none.

## Writing archives

Write the archive the way the app does, so the same pack always gives the same bytes:

1. Collect the files: `pack.json`, the included files, the referenced media, the documentation files. Nothing else.
2. Sort them by path.
3. For each file, write an entry with that path, the date 1980-01-01 00:00, no extra fields and no comment. Deflate
   `.json` files at the highest level; store every other file, with its size and CRC-32 in the local header.
4. Write no directory entries and no archive comment.

In Python, with only the standard library:

```python
import zipfile

def write_pack(files, target):
    """files: {path: bytes} of the pack; writes a deterministic .linguapack."""
    with zipfile.ZipFile(target, "w") as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0
            json_file = path.lower().endswith(".json")
            info.compress_type = zipfile.ZIP_DEFLATED if json_file else zipfile.ZIP_STORED
            archive.writestr(info, files[path], compresslevel=9)
```

[`tools/spec/build-spec.py`](https://github.com/anmx/woerds-docs/blob/main/tools/spec/build-spec.py) builds the
templates this way.

Other platforms have zip libraries with different defaults. Whatever you use, check its output:

- Stored entries must not use a data descriptor. Writers that stream often set one (bit 3 of the general purpose
  flags) for every entry; the app's streaming reader rejects it on stored entries. Write to a file or memory buffer
  that allows seeking, or choose an option that writes sizes up front.
- Timestamps, permissions and extra fields (such as extended timestamps or Unix ids) make archives differ between
  machines. Set them to fixed values or turn them off.
- Deflated bytes may differ between zlib versions and compression libraries. That is fine: the content stays the same,
  only the checksum in an index changes.

A quick check of an archive's entries, in Python:

```python
import zipfile

def archive_problems(path):
    problems = []
    for info in zipfile.ZipFile(path).infolist():
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            problems.append(f"{info.filename}: compression method {info.compress_type}")
        if info.compress_type == zipfile.ZIP_STORED and info.flag_bits & 0x08:
            problems.append(f"{info.filename}: stored entry with a data descriptor")
        if info.flag_bits & 0x01:
            problems.append(f"{info.filename}: encrypted")
    return problems
```

## Publishing in a repository

A content repository on GitHub holds the archives and a `lingua-index.json` in one folder (or below it):

```text
packs/
  lingua-index.json
  de-it/home.linguapack
  en-es/minimal.linguapack
```

1. Validate every pack; publish none with errors, and preferably none with warnings.
2. Write the archives deterministically.
3. Generate the index from the archives as they will be committed: id, path relative to the index, version, format
   version, SHA-256 and size of the file, languages, sorted content types, title, description. Sort the entries by id.
4. Commit the archives and the index together. The app reads the index from the branch the learner chose; a pack whose
   checksum does not match the index is refused.

Learners add the repository in the app as a source with owner, repository, branch and folder. The
[template index](templates/lingua-index.json) and the [index schema](schema/index.schema.json) show the format.

## Testing with the conformance cases

[`conformance/cases.json`](conformance/cases.json) lists small packs, each with the result the app's validator gives
for it:

```json
{
  "path": "invalid/sections-cycle",
  "stage": "read",
  "valid": false,
  "errors": ["sections.cycle", "sections.cycle"],
  "warnings": [],
  "description": "Two sections that are each other's parent; both are reported."
}
```

- `path` is a pack folder or a `.linguapack` file below `conformance/`.
- `errors` and `warnings` are the codes reported, as a sorted list; a code appears once per issue.
- `stage` says where the codes come from: `archive` (extracting the archive), `read` (validating the pack) or
  `import` (installing it: ids across blocks). For an `import` case, validation alone reports no error.

Use them in three ways:

- **Validator**: for each case, compare the codes your validator reports with the listed ones. Some codes cannot be
  shown by a small committed file, such as the size and file count limits; test those with generated input.
- **Reader**: every case listed as valid must open without errors; every invalid one must be refused.
- **Writer**: open each valid case and each template, save it without changes, and check that the result is valid and
  has the same content (compare the parsed JSON, not the bytes).

The cases are kept in step with the app by a test in the app's repository, so their codes are what the app reports.

## Checklist before a release

- Every template opens, saves unchanged, and validates without warnings.
- Your validator gives the listed codes for every conformance case.
- Saved archives have sorted entries, fixed dates, stored media, deflated JSON, no data descriptors on stored entries,
  and no files other than the allowed ones (no `.DS_Store`).
- Ids of existing items never change on save, and new ids never repeat old ones.
- Every save meant for sharing raises the version.
- Strings are NFC, trimmed, at most 1,000 UTF-16 units, without control characters other than tab and line feed.
- Pictures are at most 1 MiB and 2,048 pixels, still, without metadata, and described.
- A pack exported from your tool imports in the app: open the language packs (the box icon in the library, or
  Settings → Language packs) and choose *Import file* (see the [user guide](../../en/user-guide.md#language-packs)).
