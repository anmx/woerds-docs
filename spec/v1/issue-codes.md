# Issue codes of the wörds language pack format

Every problem a reader finds in a pack, an archive or a repository index has a stable code. This page lists all codes
of format version 1 with their severity and meaning, and how to fix them. The rules behind them are in the
[format specification](language-pack-format.md); the [conformance cases](conformance/cases.json) show most of them on a
small pack.

- **Error**: the pack (or index) is rejected. **Warning**: it is accepted; strict validation treats warnings as errors.
- Codes are never renamed or reused. A new reader version may add codes: an app that meets a code it does not know
  shows the issue's English message instead.
- The path of an issue names the file and the JSON path of the value, such as
  `pack.json:$.content[0].entries[2].term`, or `content/verbs.json:$.verbs[1].id` for an included file. Archive issues
  name the archive file; `content.duplicate-item` and `content.duplicate-card` name the content type.

## Contents

- [Archive](#archive)
- [Files](#files)
- [Syntax](#syntax)
- [Format version](#format-version)
- [Manifest](#manifest)
- [Sections](#sections)
- [Content](#content)
- [Vocabulary](#vocabulary)
- [Conjugation](#conjugation)
- [Repository index](#repository-index)
- [Download](#download)
- [Import](#import)

## Archive

Reported while a `.linguapack` archive is extracted. The first one stops the import.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `archive.corrupt` | Error | The archive cannot be read: it is cut off, encrypted, uses an unsupported compression method, has a stored entry with a data descriptor, or has entry names that are not UTF-8. Write it again with a standard zip writer. |
| `archive.empty` | Error | The archive has no file entries, or the file is not a zip archive at all. |
| `archive.unsafe-path` | Error | An entry name is absolute, contains `..`, `.`, an empty segment, `\`, `:` or NUL, or is longer than 255 characters. Use relative paths with `/`. |
| `archive.duplicate-entry` | Error | Two entries have the same name. |
| `archive.too-many-files` | Error | More than 10,000 entries. |
| `archive.too-large` | Error | More than 100 MiB uncompressed. |
| `archive.compression-ratio` | Error | The archive expands to more than 100 times its size (checked after the first MiB): it looks like a zip bomb. Store media instead of compressing them, and keep JSON free of huge repetitive content. |

## Files

The set of files in the pack, included files and referenced pictures and recordings.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `files.symlink` | Error | The pack folder contains a symbolic link. Replace it with the file. |
| `files.too-many` | Error | More than 10,000 files. |
| `files.pack-too-large` | Error | All files together exceed 100 MiB. |
| `files.disallowed-type` | Error | A file that is not `.json`, `.opus`, `.m4a`, `.mp3`, `.png`, `.webp` or a `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `NOTICE` or `README.md`. Often `.DS_Store` or `Thumbs.db`: leave them out. |
| `files.missing` | Error | `pack.json`, an included file or a referenced file does not exist. Paths are case-sensitive and relative to the pack root. |
| `files.too-large` | Error | `pack.json` or an included file is larger than 5 MiB. Split the content into more included files. |
| `files.unsafe-path` | Error | An include or a reference is not a safe relative path. |
| `files.include-not-json` | Error | An entry of `includes` does not end in `.json`. |
| `files.wrong-kind` | Error | A referenced file has the wrong extension for its field: `image` takes `.png` or `.webp`, `audio` takes `.opus`, `.m4a` or `.mp3`. |
| `files.content-mismatch` | Error | The file's bytes do not match its extension, or a picture has no readable header. Convert the file instead of renaming it. |
| `files.image-too-large` | Error | A picture is larger than 1 MiB. |
| `files.image-dimensions` | Error | A picture is wider or taller than 2,048 pixels. |
| `files.image-animated` | Error | A picture is animated (APNG or animated WebP). Use a still picture. |

## Syntax

Reading `pack.json` and included files.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `syntax.invalid-json` | Error | Not valid JSON: a byte order mark, a comment, a trailing comma, single quotes, or broken text. |
| `syntax.schema` | Error | The JSON does not have the expected structure: an unknown field, a missing required field, a value of the wrong type, or an included file that holds something other than one object. Compare with the schema. |
| `syntax.string-too-long` | Error | A string is longer than 1,000 characters after NFC normalization. |
| `syntax.control-character` | Error | A string contains a control character other than line feed or tab, such as a carriage return. |

## Format version

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `format.unsupported-version` | Error | `formatVersion` is higher than the reader supports. Write `1`. |
| `format.invalid-version` | Error | `formatVersion` is below 1. |
| `format.app-too-old` | Error | `minAppFormatVersion` is higher than the reader supports. Leave it out in version 1. |

## Manifest

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `manifest.invalid-id` | Error | The pack id is not lowercase segments of letters and digits joined by `.`, `_` or `-`, or longer than 100 characters. |
| `manifest.invalid-version` | Error | The version is not a semantic version such as `1.0.0`. |
| `manifest.blank-title` | Error | The title is empty or only white space. |
| `manifest.missing-license` | Warning | No license is declared. Add an SPDX identifier, or `NONE`. |
| `manifest.invalid-language` | Error | `sourceLanguage`, `targetLanguage` or `tts.locale` is not a language tag such as `de`, `pt-BR` or `zh-Hant-TW`. |
| `manifest.same-languages` | Error | Source and target language have the same primary language, such as `de` and `de-AT`. |
| `manifest.tts-language-mismatch` | Warning | `tts.locale` is in another language than the target language. |
| `manifest.no-directions` | Error | `supportedDirections` is an empty list. Leave it out for both directions. |
| `manifest.invalid-direction` | Error | A direction is neither `source->target` nor `target->source`. |

## Sections

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `sections.invalid-id` | Error | A section id does not match the id pattern, or is longer than 100 characters. |
| `sections.duplicate-id` | Error | Two sections have the same id. |
| `sections.blank-title` | Error | A section title is empty or only white space. |
| `sections.unknown-parent` | Error | `parentId` names no section of the pack. |
| `sections.cycle` | Error | Following the parents of a section leads back to it. Reported for every section in the cycle. |

## Content

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `content.empty` | Error | The pack has no content blocks, inline or included. |
| `content.missing-type` | Error | A content block has no string `type`. |
| `content.unknown-type` | Warning | A block has a type the reader does not know; it is skipped. |
| `content.no-supported-type` | Error | No block of a type the reader knows is left. |
| `content.duplicate-item` | Error | Two blocks of the same type define an item with the same id. Reported when the pack is installed. |
| `content.duplicate-card` | Error | Two blocks of the same type define the same card. Reported when the pack is installed, together with `content.duplicate-item`. |

## Vocabulary

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `vocabulary.no-entries` | Error | A vocabulary block has no entries. |
| `vocabulary.invalid-id` | Error | An entry id does not match the id pattern, or is longer than 100 characters. |
| `vocabulary.duplicate-entry` | Error | Two entries of one block have the same id. |
| `vocabulary.duplicate-term` | Warning | The same term with the same translation appears twice. |
| `vocabulary.blank` | Error | A text field is present but empty or only white space. Leave it out instead. |
| `vocabulary.no-section` | Warning | An entry belongs to no section. Not reported for packs whose id starts with `user.`. |
| `vocabulary.unknown-section` | Error | An id in `sectionIds` names no section of the pack. |
| `vocabulary.invalid-part-of-speech` | Error | `partOfSpeech` is not one of the eleven allowed values. |
| `vocabulary.invalid-gender` | Error | `gender` is not `m`, `f`, `n` or `mf`. |
| `vocabulary.no-image-description` | Warning | An entry has a picture without `imageDescription`; screen readers cannot describe it. |
| `vocabulary.description-without-image` | Warning | An entry has `imageDescription` but no picture; the description is ignored. |

## Conjugation

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `conjugation.no-persons` | Error | A conjugation block has no persons. |
| `conjugation.no-tenses` | Error | A conjugation block has no tenses. |
| `conjugation.no-verbs` | Error | A conjugation block has no verbs. |
| `conjugation.invalid-id` | Error | A person, tense or verb id does not match the id pattern, or is longer than 100 characters. |
| `conjugation.duplicate-id` | Error | Two persons or two tenses of one block have the same id. |
| `conjugation.duplicate-verb` | Error | Two verbs of one block have the same id. |
| `conjugation.blank` | Error | A label, prompt, infinitive, translation, answer or speech text is empty or only white space. |
| `conjugation.no-section` | Warning | A verb belongs to no section. |
| `conjugation.unknown-section` | Error | An id in `sectionIds` names no section of the pack. |
| `conjugation.no-forms` | Error | A verb has no conjugations. |
| `conjugation.unknown-tense` | Error | A conjugation names a tense the block does not define. |
| `conjugation.duplicate-tense` | Error | A verb is conjugated twice in the same tense. |
| `conjugation.unknown-person` | Error | A form names a person the block does not define. |
| `conjugation.duplicate-form` | Error | A tense of a verb has two forms of the same person. |
| `conjugation.generated-prompt` | Warning | A form has no prompt; the app shows the person and the translation instead. |
| `conjugation.incomplete-grid` | Warning | A tense of a verb lacks forms for some persons. |

## Repository index

Reading `lingua-index.json`. The first four reject the whole index; the others skip one entry, so the rest of the
repository stays available.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `index.too-large` | Error | The index is larger than 1 MiB. |
| `index.syntax` | Error | The index is not valid JSON, or a required field is missing or has the wrong type. |
| `index.unsupported-version` | Error | `indexVersion` is not 1. |
| `index.too-many-packs` | Error | The index lists more than 1,000 packs. |
| `index.duplicate-id` | Warning | A pack id is listed more than once; the first entry is used. |
| `index.invalid-id` | Warning | An entry's id is not a valid pack id. |
| `index.unsafe-path` | Warning | An entry's path leaves the repository folder. |
| `index.invalid-extension` | Warning | An entry's path does not end in `.linguapack`, or has characters other than `A`–`Z`, `a`–`z`, `0`–`9`, `.`, `_`, `-` and `/`. |
| `index.invalid-version` | Warning | An entry's version is not a semantic version. |
| `index.unsupported-format` | Warning | An entry's format version is not supported. |
| `index.invalid-sha256` | Warning | An entry's checksum is not 64 hex digits. |
| `index.invalid-language` | Warning | An entry's source or target language is not a language tag. |
| `index.no-content-types` | Warning | An entry lists no content types. |
| `index.invalid-content-type` | Warning | A content type is not an id of at most 50 characters. |
| `index.invalid-title` | Warning | An entry's title is blank, longer than 200 characters, or contains control characters other than line feeds. |
| `index.invalid-description` | Warning | An entry's description is longer than 1,000 characters or contains control characters other than line feeds. |
| `index.invalid-size` | Warning | An entry's size is not between 1 byte and 100 MiB. |

## Download

Checked after a pack is downloaded from a repository, before it is imported.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `download.size-mismatch` | Error | The archive's size differs from `sizeBytes` in the index. Generate the index from the final archives. |
| `download.sha256-mismatch` | Error | The archive's SHA-256 differs from `sha256` in the index. |
| `download.index-mismatch` | Error | The archive's pack id or version differs from the index entry. |

## Import

Checks of the app when it installs a pack that is valid in itself.

| Code | Severity | Meaning and fix |
| --- | --- | --- |
| `import.user-pack-conflict` | Error | A pack with a `user.` id came from a repository, and the learner has an editable pack with that id. Publish packs under ids without the `user.` prefix. |
| `import.not-editable` | Error | A local file with a `user.` id cannot become an editable pack: it has no vocabulary entries, an entry id is used twice, a title is longer than 100 characters, or a picture has no description. See section 13 of the specification. |
