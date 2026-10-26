# wörds language pack format, version 1

This document specifies the language packs that the flashcard app wörds imports: their archive, their files, the
manifest `pack.json`, the content blocks, the rules a valid pack follows and the repository index that offers packs
for download. It is written for developers of tools that create, convert or edit packs outside the app, for example
web, macOS or Windows editors.

Specification revision 1.0 of 2026-10-26, for format version 1. It describes the behaviour of wörds 0.11.1. The text
is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the schemas, templates and conformance
cases are [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

## Contents

- [1. Introduction](#1-introduction)
- [2. Overview](#2-overview)
- [3. Archive](#3-archive)
- [4. Files in a pack](#4-files-in-a-pack)
- [5. JSON and text](#5-json-and-text)
- [6. Manifest](#6-manifest)
- [7. Sections](#7-sections)
- [8. Content blocks](#8-content-blocks)
- [9. Vocabulary blocks](#9-vocabulary-blocks)
- [10. Conjugation blocks](#10-conjugation-blocks)
- [11. Media files](#11-media-files)
- [12. Identity, progress and updates](#12-identity-progress-and-updates)
- [13. Editable packs](#13-editable-packs)
- [14. Validation](#14-validation)
- [15. Repository index](#15-repository-index)
- [16. Security considerations](#16-security-considerations)
- [17. Appendix](#17-appendix)

## 1. Introduction

A **language pack** is a set of flashcards for one language pair: words with their translations, verb forms, and the
lections (sections) of a course or textbook. Learners install packs from a file, from a GitHub repository, or make
their own in the app. The app turns each pack into cards and schedules them with spaced repetition.

This specification is accompanied by:

- [`schema/pack.schema.json`](schema/pack.schema.json): the JSON Schema (draft 2020-12) of `pack.json` and of
  included content files. It is generated from the app's code and covers the structure; section 14 lists what it
  cannot check.
- [`schema/index.schema.json`](schema/index.schema.json): the JSON Schema of the repository index.
- [Issue codes](issue-codes.md): every code a reader reports, with its severity and meaning.
- [Implementers' guide](implementers-guide.md): non-normative advice for building an editor.
- [`templates/`](templates/): example packs, as directories and as `.linguapack` archives, and an example index.
- [`conformance/`](conformance/): small packs that each break or exercise one rule, listed with the codes a reader
  reports for them in [`conformance/cases.json`](conformance/cases.json).

The app is the reference reader. Its validator is not distributed on its own; the conformance cases are kept in step
with it by a test in the app's repository.

### Conventions

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED, MAY and OPTIONAL are to be interpreted as in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and
only when, they appear in all capitals.

- A **reader** is software that imports packs (the app). A **writer** is software that creates or changes packs.
- The **source language** is the language the learner knows; the **target language** is the one being learned.
- Issue codes are written like `manifest.invalid-id`. Their severity is **error** (the pack is rejected) or
  **warning** (the pack is accepted).
- **Characters** are counted in UTF-16 code units, after Unicode NFC normalization (section 5). Most characters are
  one unit; characters outside the Basic Multilingual Plane, such as most emoji, are two.
- **MiB** is 1,048,576 bytes.

### Conformance

- A **conforming pack** is one for which a reader reports no error.
- A **conforming writer** MUST produce only conforming packs and SHOULD produce packs without warnings. The app's own
  tooling validates packs in strict mode, which treats warnings as errors.
- A **conforming reader** MUST reject every pack for which this specification names an error, and SHOULD report each
  problem with the code given here.

## 2. Overview

A pack is distributed as a zip archive with the extension `.linguapack`. Unpacked, it is a directory:

| Path | Required | Content |
| --- | --- | --- |
| `pack.json` | yes | The manifest: id, version, title, languages, sections, and the content blocks or the files that hold them |
| `content/*.json` | no | Content blocks in their own files, listed in the manifest's `includes` |
| `images/`, `audio/` | no | Pictures and recordings referenced from the content |
| `LICENSE`, `NOTICE`, `README.md` | no | Documentation; ignored by the app |

Only `pack.json` has a fixed place: the root of the archive. The other paths are conventions; any path that follows
section 4 works.

A complete minimal pack, with one lection and three words:

```json
{
  "formatVersion": 1,
  "id": "org.example.en-es.minimal",
  "version": "1.0.0",
  "title": "Spanish: first words",
  "license": "CC0-1.0",
  "sourceLanguage": "en",
  "targetLanguage": "es",
  "sections": [
    { "id": "greetings", "title": "Greetings" }
  ],
  "content": [
    {
      "type": "vocabulary",
      "entries": [
        { "id": "hola", "term": "hola", "translation": "hello", "sectionIds": ["greetings"] },
        { "id": "adios", "term": "adiós", "translation": "goodbye", "sectionIds": ["greetings"] },
        { "id": "gracias", "term": "gracias", "translation": "thank you", "sectionIds": ["greetings"] }
      ]
    }
  ]
}
```

Two content types exist in format version 1: **vocabulary** (words and phrases, section 9) and **conjugation** (verb
forms by person and tense, section 10). A pack may contain blocks of both.

## 3. Archive

A `.linguapack` file is a zip archive as specified in PKWARE's
[APPNOTE.TXT](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT). The root of the archive is the root of the
pack: `pack.json` MUST be a top-level entry, not inside a folder.

Readers read the archive as a stream, entry by entry from the local file headers; they do not use the central
directory. Therefore:

- Entries MUST use the compression method **stored** (0) or **deflate** (8). Encryption is not supported.
- A **stored** entry MUST carry its sizes and CRC-32 in the local file header, without a data descriptor. Deflated
  entries MAY use a data descriptor. Several zip libraries write data descriptors by default when they write to a
  stream; check what yours does.
- Entry names MUST be UTF-8. Directory entries (names ending in `/`) are allowed and ignored.

Every entry name MUST be a **safe relative path**:

- at most 255 characters, separated by `/`;
- not starting with `/`, without empty segments, and without the segments `.` or `..`;
- without `\`, `:` or the NUL character.

Readers MUST reject the whole archive at the first entry that breaks a rule, and report:

| Code | When |
| --- | --- |
| `archive.unsafe-path` | An entry name is not a safe relative path |
| `archive.duplicate-entry` | Two entries have the same name |
| `archive.too-many-files` | More than 10,000 entries |
| `archive.too-large` | More than 100 MiB uncompressed in total |
| `archive.compression-ratio` | Once more than 1 MiB has been extracted, the extracted bytes exceed 100 times the archive bytes read so far |
| `archive.empty` | The archive has no file entries (a file that is not a zip archive at all also ends here, since a stream reader finds no entry in it) |
| `archive.corrupt` | The archive cannot be read, for example because it ends early |

Readers measure sizes and the compression ratio on the bytes they actually read and write, never on the sizes the
archive declares.

### Deterministic archives

Writers SHOULD write archives so that the same pack always gives the same bytes, as the app does when it exports a
pack. The checksum in a repository index (section 15) then only changes when the content changes. The app writes:

- entries in ascending order of their path (compared as strings), without directory entries;
- the modification time 1980-01-01 00:00 on every entry, and no extra fields;
- `.json` files deflated at the highest compression level; pictures and audio stored, since they are compressed
  already.

### Directories

Where packs are kept in a folder rather than an archive, for example in a content repository, the folder is the pack
root. Symbolic links MUST NOT appear in it (`files.symlink`); readers never follow them.

## 4. Files in a pack

A pack MAY contain only these files:

- files whose name ends in `.json`, `.opus`, `.m4a`, `.mp3`, `.png` or `.webp` (the extension is compared without
  regard to case);
- documentation files named exactly `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `NOTICE` or `README.md`, in any folder.

Any other file is an error (`files.disallowed-type`). This includes files that operating systems create on their own,
such as `.DS_Store`, `Thumbs.db` or `desktop.ini`: writers MUST NOT include them. A `__MACOSX/` folder, which some zip
tools add, holds files with the same extensions as the originals; it is not an error, but it is dead weight, and
writers SHOULD NOT include it either.

| Limit | Value | Code |
| --- | --- | --- |
| Files in the pack | at most 10,000 | `files.too-many` |
| Total size of all files | at most 100 MiB | `files.pack-too-large` |
| Size of `pack.json` | at most 5 MiB | `files.too-large` |
| Size of each included JSON file | at most 5 MiB | `files.too-large` |
| Size of each picture | at most 1 MiB | `files.image-too-large` |

Files that nothing references are allowed, but they are carried along for nothing. Writers SHOULD include only the
media that the content references; the app's own exports do.

## 5. JSON and text

`pack.json` and every included file MUST be JSON as defined by [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259),
encoded in UTF-8 **without** a byte order mark. Readers parse strictly and report `syntax.invalid-json` for:

- a byte order mark, comments, trailing commas, single quotes or unquoted keys;
- `NaN`, `Infinity` and other non-standard values.

The structure MUST match the schema (`syntax.schema`):

- **Unknown fields are errors**, in the manifest and in every content block. The only exception is `$schema`, which
  the manifest and the top level of an included file MAY carry so that text editors can find the schema. Readers
  ignore it.
- Required fields MUST be present, and every value MUST have the type the schema gives.
- An optional field SHOULD be left out when it has no value. `null` is accepted for the optional fields whose schema
  allows it, but a list such as `authors` or `sectionIds` MUST NOT be `null`.
- An object MUST NOT contain the same key twice.

The app's reader is lenient in one respect that is **not** part of the format: it also accepts a number or a boolean
written as a string (`"formatVersion": "1"`, `"irregular": "true"`). Writers MUST NOT rely on this; other readers may
reject such packs.

### Strings

Every string in every JSON file, including ids and paths, follows these rules:

- Readers normalize every string to **Unicode NFC** before any other check and before they store it. So `ä` written as
  `a` followed by a combining diaeresis equals the precomposed `ä`. Writers SHOULD write NFC.
- After normalization a string MUST NOT be longer than **1,000 characters** (`syntax.string-too-long`).
- A string MUST NOT contain control characters (U+0000–U+001F and U+007F–U+009F) except the line feed (U+000A) and the
  tab (U+0009) (`syntax.control-character`). The carriage return is not allowed: line breaks inside a value are
  written as `\n` alone.
- Where a value MUST NOT be **blank**, it MUST contain at least one character that is not white space.
- Readers trim surrounding white space from the pack title, the description, the license and the section titles. They
  keep the other texts as written, so writers SHOULD trim them.

## 6. Manifest

`pack.json` is a JSON object with these fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `$schema` | string | no | URI of the schema, for text editors; ignored |
| `formatVersion` | integer | yes | The format version the pack is written in; `1` for this specification |
| `minAppFormatVersion` | integer | no | The lowest format version a reader must support to use the pack |
| `id` | string | yes | Stable, globally unique id of the pack |
| `version` | string | yes | Semantic version of the pack |
| `title` | string | yes | Title shown in the app |
| `description` | string | no | One or two sentences about the pack |
| `license` | string | no, but expected | SPDX license identifier of the content |
| `authors` | array of strings | no | Names of the authors |
| `sourceLanguage` | string | yes | Language tag of the language the learner knows |
| `targetLanguage` | string | yes | Language tag of the language being learned |
| `tts` | object | no | `{ "locale": "<language tag>" }`: the voice for speech synthesis of the target language |
| `supportedDirections` | array of strings | no | The study directions the pack allows |
| `sections` | array of objects | no | The pack's sections (lections), section 7 |
| `content` | array of objects | no | Content blocks, section 8 |
| `includes` | array of strings | no | Paths of JSON files that each hold one content block |

### Format version

- `formatVersion` MUST be `1`. A reader reports `format.unsupported-version` for a higher value and
  `format.invalid-version` for a value below 1.
- `minAppFormatVersion` is reserved for later format versions. In version 1 writers SHOULD leave it out; a value
  above 1 makes readers report `format.app-too-old`.

### Id

- The id MUST match `^[a-z0-9]+([._-][a-z0-9]+)*$` and MUST NOT be longer than 100 characters
  (`manifest.invalid-id`): lowercase letters and digits in segments joined by `.`, `_` or `-`.
- It identifies the pack for good: updates replace the installed pack with the same id, and learning progress is
  stored by it (section 12). Writers MUST NOT change the id of a published pack.
- Writers SHOULD make ids globally unique with a reversed domain name or another prefix they control, for example
  `org.example.de-it.a1`.
- Ids starting with `user.` mark packs that the app imports as editable (section 13). Writers MUST use the prefix only
  for packs meant to be edited in the app, and MUST NOT use it for packs they publish for installation.

### Version

- The version MUST be a [semantic version 2.0.0](https://semver.org/spec/v2.0.0.html) of three numbers, such as
  `1.4.0` or `2.0.0-beta.1` (`manifest.invalid-version`).
- Readers compare versions number by number. A pre-release sorts before its release; two pre-release labels are
  compared as plain strings, so `1.0.0-beta.10` sorts before `1.0.0-beta.9`. Build metadata (`+…`) is ignored.
- Every published change MUST raise the version (section 12).

### Title, description, license and authors

- `title` MUST NOT be blank (`manifest.blank-title`). Short titles read best in the app's lists; the app's own editor
  allows at most 100 characters.
- `license` SHOULD be an [SPDX license identifier](https://spdx.org/licenses/) or expression, such as `CC-BY-4.0`,
  for the content of the pack. A missing or blank license is a warning (`manifest.missing-license`). The value `NONE`
  states that no license is granted; the app writes it for own packs without a chosen license.
- The licenses of third-party pictures and recordings SHOULD be named in a `NOTICE` or `LICENSE` file in the pack.

### Languages

- `sourceLanguage`, `targetLanguage` and `tts.locale` MUST be language tags of the form language, optional script,
  optional region: `^[a-zA-Z]{2,3}(-[a-zA-Z]{4})?(-([a-zA-Z]{2}|[0-9]{3}))?$` (`manifest.invalid-language`). This is
  a subset of [BCP 47](https://www.rfc-editor.org/info/bcp47): `de`, `pt-BR`, `zh-Hant-TW` and `es-419` are valid;
  variants and extensions such as `de-CH-1901` are not.
- Writers SHOULD use the canonical case: language in lower case, script in title case, region in upper case.
- The primary languages (the part before the first `-`, compared without regard to case) of `sourceLanguage` and
  `targetLanguage` MUST differ (`manifest.same-languages`).
- `tts.locale` defaults to `targetLanguage`. Its primary language SHOULD be that of the target language
  (`manifest.tts-language-mismatch`, a warning). Set it to choose a regional voice, such as `it-IT` for `it`.

### Directions

- `source->target` is **production**: the card shows the source language and the learner recalls the target language.
- `target->source` is **recognition**: the card shows the target language and the learner recalls the meaning.
- Without `supportedDirections` (or with `null`) both directions are allowed. A list MUST contain at least one entry
  (`manifest.no-directions`) and only these two values (`manifest.invalid-direction`).
- Each card is learned separately in each allowed direction; the learner can narrow the choice in the app.

### Content and includes

The pack MUST contain at least one content block (`content.empty`), either inline in `content` or as a file listed in
`includes`. Readers use the blocks of `content` first, then those of `includes`, in the listed order. Within a type,
that order decides the order in which learners meet new cards (sections 9 and 10).

## 7. Sections

Sections structure a pack like the units and chapters of a course. The app calls them lections; learners choose
them for a session and see statistics by section.

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Id, unique within the pack; same rules as the pack id |
| `title` | string | yes | Title shown in the app; MUST NOT be blank |
| `order` | integer | no | Position among its siblings; default `0` |
| `parentId` | string | no | Id of the enclosing section, for nested units |

Rules:

- Ids MUST match the id pattern and be at most 100 characters (`sections.invalid-id`), and MUST be unique within the
  pack (`sections.duplicate-id`).
- Titles MUST NOT be blank (`sections.blank-title`).
- `parentId` MUST name a section of the pack (`sections.unknown-parent`), and following the parents MUST NOT lead back
  to the section itself (`sections.cycle`). Sections MAY be nested to any depth and listed in any order.
- The app shows sibling sections ordered by `order`, then by title. Writers SHOULD give every section an explicit
  `order`.
- A section MAY be empty, for example a unit that only holds sub-sections.

Items (vocabulary entries and verbs) name their sections in `sectionIds`. An item MAY belong to several sections; the
first one that exists in the pack decides the group the item is studied in. An item in no section is a warning, except
in editable packs (section 13).

## 8. Content blocks

A content block is a JSON object with a `type` and the fields of that type.

- A block without a string `type` is an error (`content.missing-type`).
- A block of a type the reader does not know is skipped with a warning (`content.unknown-type`). This is the format's
  extension point: a pack can carry blocks for newer apps next to blocks every app understands. A pack MUST contain
  at least one block of a known type (`content.no-supported-type`).
- Format version 1 defines the types `vocabulary` (section 9) and `conjugation` (section 10).

### Included files

Each path in `includes` names a JSON file with exactly one content block.

- The path MUST be a safe relative path, as for archive entries (`files.unsafe-path`), and end in `.json`
  (`files.include-not-json`).
- The file MUST exist (`files.missing`), be at most 5 MiB (`files.too-large`) and contain one JSON object
  (`syntax.schema`). Its top level MAY carry `$schema`; the schema's definition for it is
  `pack.schema.json#/$defs/contentBlock`.
- An include that fails adds no block. If it was the only one, the pack has no content (`content.empty`).
- Paths inside an included block, such as pictures, are relative to the **pack root**, not to the included file.

### Ids across blocks

Item ids MUST be unique among all blocks of the same type: two vocabulary blocks MUST NOT both define the entry
`casa`. Each type checks duplicates within one block itself. Duplicates across blocks are found when the pack is
installed and reported as `content.duplicate-item` and `content.duplicate-card`; the app then installs nothing.

## 9. Vocabulary blocks

A vocabulary block holds words and phrases. Each entry becomes one card.

```json
{
  "type": "vocabulary",
  "entries": [
    {
      "id": "casa",
      "term": "la casa",
      "translation": "das Haus",
      "partOfSpeech": "noun",
      "gender": "f",
      "plural": "le case",
      "sectionIds": ["unit-1"],
      "example": { "target": "La casa è grande.", "source": "Das Haus ist groß." },
      "image": "images/house.png",
      "imageDescription": "Ein kleines Haus mit rotem Dach"
    }
  ]
}
```

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Id of the entry; same rules as the pack id |
| `term` | string | yes | The word or phrase in the target language; nouns with their article, such as `la casa` |
| `translation` | string | yes | Its meaning in the source language, such as `das Haus` |
| `partOfSpeech` | string | no | `noun`, `verb`, `adjective`, `adverb`, `pronoun`, `preposition`, `conjunction`, `interjection`, `numeral`, `article` or `phrase` |
| `gender` | string | no | Grammatical gender of the term: `m`, `f`, `n`, or `mf` for both (`il/la cantante`) |
| `plural` | string | no | The plural in the target language, with its article, such as `le case` |
| `sectionIds` | array of strings | no | The sections the entry belongs to |
| `example` | object | no | `{ "target": "…", "source": "…" }`: an example sentence and its translation, both required |
| `audio` | string | no | Path of a recording of the term (section 11) |
| `tts` | string | no | Text for speech synthesis when it should differ from the term |
| `image` | string | no | Path of a still picture of the meaning (section 11) |
| `imageDescription` | string | no | What the picture shows, in the source language; read by screen readers |
| `sourceHint` | string | no | A second line under the translation, for example to tell meanings apart |
| `targetHint` | string | no | A second line under the term; replaces the plural there |

Rules:

- A block MUST have at least one entry (`vocabulary.no-entries`).
- Entry ids MUST match the id pattern and be at most 100 characters (`vocabulary.invalid-id`), and MUST be unique in
  the block (`vocabulary.duplicate-entry`) and among all vocabulary blocks of the pack (section 8).
- No text field MAY be blank when present (`vocabulary.blank`).
- `partOfSpeech` and `gender` MUST be one of the listed values (`vocabulary.invalid-part-of-speech`,
  `vocabulary.invalid-gender`).
- Every id in `sectionIds` MUST name a section of the pack (`vocabulary.unknown-section`). An entry without sections
  is a warning (`vocabulary.no-section`), except in packs whose id starts with `user.`.
- The same term with the same translation twice is a warning (`vocabulary.duplicate-term`).
- An `image` without `imageDescription` is a warning (`vocabulary.no-image-description`), and so is an
  `imageDescription` without an `image`, which is ignored (`vocabulary.description-without-image`).

### How the app uses vocabulary fields

This part is informative. It helps writers fill the fields so that the cards work well.

- The source side of a card shows `translation`, with `sourceHint` below it. The target side shows `term`, with
  `targetHint` below it, or else `plural`. The library lists the entry by `term` and `translation`, with the part of
  speech as a badge, and the detail pane adds the gender, the plural, the example and the picture. Search covers the
  term, the translation, the plural and the example.
- The term is spoken by playing `audio`, or else by speech synthesis of `tts`, or else of the term. For speech
  synthesis, a word with a slash alternative is reduced to its first form: `il/la cantante` is spoken as
  `il cantante`.
- Typed answers compare what the learner types with the side being asked. Case, spacing, typographic apostrophes and
  final punctuation do not matter. `,`, `;` and a slash between spaces (` / `) separate alternatives that are each
  accepted; a slash inside a word offers a choice (`stato/a`); text in parentheses is a note that need not be typed.
  A subject pronoun at the start of the answer may be left out; a missing article makes the answer almost right.
- The article drill asks for the article of nouns. It takes the article from the term as written (`la casa`,
  `l'acqua`), so nouns SHOULD be written with their definite article. German falls back to `gender`. Nouns with the
  gender `mf` are left out.
- Entries are grouped by their first section, in the order in which the sections first occur among the entries, and
  each group is split into sets of ten for sessions. New cards are introduced in that order. Write entries in the
  order learners should meet them and keep each section's entries together.

## 10. Conjugation blocks

A conjugation block holds verbs with their forms by tense and person. Each form becomes one card. Persons and tenses
are defined once per block, so the block works for any language.

```json
{
  "type": "conjugation",
  "persons": [
    { "id": "1s", "label": "io", "prompt": "I" },
    { "id": "2s", "label": "tu", "prompt": "you" }
  ],
  "tenses": [
    { "id": "presente", "label": "Presente", "sourceLabel": "Present" }
  ],
  "verbs": [
    {
      "id": "essere",
      "infinitive": "essere",
      "translation": "to be",
      "sectionIds": ["lesson-1"],
      "irregular": true,
      "conjugations": [
        {
          "tenseId": "presente",
          "forms": [
            { "personId": "1s", "prompt": "I am", "answer": "io sono" },
            { "personId": "2s", "prompt": "you are", "answer": "tu sei" }
          ]
        }
      ]
    }
  ]
}
```

| Object | Field | Type | Required | Meaning |
| --- | --- | --- | --- | --- |
| block | `persons` | array | yes | The grammatical persons, in display order |
| block | `tenses` | array | yes | The tenses, in display order |
| block | `verbs` | array | yes | The verbs |
| person | `id` | string | yes | Id, unique in the block, such as `1s` |
| person | `label` | string | yes | The target-language pronoun, such as `io` |
| person | `prompt` | string | yes | The source-language pronoun, such as `I` |
| tense | `id` | string | yes | Id, unique in the block, such as `presente` |
| tense | `label` | string | yes | The tense's name in the target language, such as `Presente` |
| tense | `sourceLabel` | string | no | Its name in the source language, such as `Present` |
| verb | `id` | string | yes | Id of the verb; unique among all conjugation blocks of the pack |
| verb | `infinitive` | string | yes | The infinitive in the target language |
| verb | `translation` | string | yes | Its meaning in the source language |
| verb | `sectionIds` | array of strings | no | The sections the verb belongs to |
| verb | `irregular` | boolean | no | Marks the verb as irregular; default `false` |
| verb | `conjugations` | array | yes | One object per tense: `tenseId` and `forms` |
| form | `personId` | string | yes | The person of the form |
| form | `prompt` | string | no | The source-language form shown on the card, such as `I am` |
| form | `answer` | string | yes | The target-language form with its pronoun, such as `io sono` |
| form | `audio` | string | no | Path of a recording of the answer (section 11) |
| form | `tts` | string | no | Text for speech synthesis when it should differ from the answer |
| form | `sourceHint` | string | no | A second line under the prompt |
| form | `targetHint` | string | no | A second line under the answer |

Rules:

- A block MUST have at least one person (`conjugation.no-persons`), one tense (`conjugation.no-tenses`) and one verb
  (`conjugation.no-verbs`).
- Person, tense and verb ids MUST match the id pattern and be at most 100 characters (`conjugation.invalid-id`).
  Person and tense ids MUST be unique in their list (`conjugation.duplicate-id`), verb ids in the block
  (`conjugation.duplicate-verb`) and among all conjugation blocks of the pack (section 8).
- Labels, prompts, infinitives, translations, answers and `tts` texts MUST NOT be blank (`conjugation.blank`).
- Every id in `sectionIds` MUST name a section (`conjugation.unknown-section`). A verb without sections is a warning
  (`conjugation.no-section`).
- A verb MUST have at least one conjugation (`conjugation.no-forms`). Each `tenseId` MUST name a tense of the block
  (`conjugation.unknown-tense`) and appear once per verb (`conjugation.duplicate-tense`).
- Each `personId` MUST name a person of the block (`conjugation.unknown-person`) and appear once per tense
  (`conjugation.duplicate-form`).
- A form without `prompt` is a warning (`conjugation.generated-prompt`): the app then shows the person's prompt and the
  verb's translation, such as `I (to be)`. Writers SHOULD write prompts, especially for inflected source languages.
- A tense that lacks forms for some persons is a warning (`conjugation.incomplete-grid`). Leave persons out on purpose
  only, for example for impersonal verbs.

### How the app uses conjugation fields

Informative. The card shows the prompt with the tense's `sourceLabel` (or `label`) below it, or the form's
`sourceHint` instead; the answer side shows the answer with the infinitive and the tense label below it, or the
`targetHint` instead. Speech uses `audio`, `tts` or the answer reduced as for vocabulary. Sessions group forms by verb
and tense; tenses and persons follow the order of their lists. The library shows each verb with its full grid and an
"irregular" badge.

## 11. Media files

Content refers to pictures and recordings by their path relative to the pack root, such as `images/house.png`. The
same file MAY be referenced several times.

| Kind | Extensions | Signature the reader checks |
| --- | --- | --- |
| Audio | `.opus` | Ogg container: the file starts with `OggS` |
| Audio | `.m4a` | MPEG-4 container: `ftyp` at byte 4 |
| Audio | `.mp3` | An `ID3` tag at the start, or an MPEG audio frame sync (11 set bits) |
| Picture | `.png` | The PNG signature, then an `IHDR` chunk |
| Picture | `.webp` | `RIFF`, then `WEBP` at byte 8, with a `VP8`, `VP8L` or `VP8X` chunk (`VP8` followed by a space) |

Rules, checked for every referenced file:

- The path MUST be a safe relative path (`files.unsafe-path`).
- The extension MUST fit the field: `audio` takes audio, `image` takes pictures (`files.wrong-kind`).
- The file MUST exist (`files.missing`) and start with the signature of its extension (`files.content-mismatch`).
- A picture MUST be at most 1 MiB (`files.image-too-large`) and 2,048 × 2,048 pixels (`files.image-dimensions`), as
  its header states, and MUST NOT be animated (`files.image-animated`): no `acTL` chunk before the image data of a
  PNG, no animation flag in a WebP `VP8X` header.

Readers check signatures and headers only; they do not decode the files before they use them. A file that passes the
checks but cannot be decoded fails when it is shown or played. Writers MUST write complete, decodable files.

Recommendations:

- Pictures: square, 512 to 1,024 pixels, WebP or PNG, without metadata chunks. The app's own editor stores pictures as
  WebP of at most 1,024 pixels. Every picture SHOULD have an `imageDescription`.
- Recordings: short clips of the term or form alone, without leading silence. Opus is the most compact choice.

## 12. Identity, progress and updates

### Card keys

The app stores learning progress by **card key**, without a link to the installed pack, so progress survives updates,
removal and reinstalling. A card key is made of four parts, joined by `|`:

1. the pack id;
2. the content type, `vocabulary` or `conjugation`;
3. the item id: the entry id, or the verb id;
4. the variant: `term` for a vocabulary entry, `<tenseId>/<personId>` for a verb form.

For example `org.example.de-it.home|vocabulary|casa|term` and
`org.example.en-it.verbs|conjugation|essere|presente/1s`. Each card is scheduled separately in each study direction.
Ids never contain `|` or `/`, so the keys are unambiguous.

What happens to progress when a pack changes:

| Change | Progress |
| --- | --- |
| Edit any text, picture or recording | Kept |
| Move an item to another section, or reorder items | Kept |
| Add items | New cards start fresh |
| Remove an item | Its card disappears; the progress returns if an item with the same id comes back |
| Change an entry id or a verb id | Lost for that item: it is a new card |
| Change a tense id or a person id | Lost for every form of that tense or person |
| Move an item between content types | Lost |
| Change the pack id | Lost for the whole pack: it is a different pack |

Therefore writers:

- MUST keep the ids of existing packs, sections, items, tenses and persons when they change a pack;
- MUST give new items ids that no other item of the same type in the pack has, now or earlier, unless the new item
  is meant to continue that item's progress;
- SHOULD NOT derive ids from text in a way that makes them change when the text is corrected. Derive an id once when
  the item is created, then keep it.

### Updates

A pack is updated by importing a pack with the same id. The app compares the versions:

- a **higher** version replaces the installed pack;
- the **same** version replaces it if the content differs, and does nothing if it is identical;
- a **lower** version is refused as a downgrade (only the packs built into the app are silently ignored instead).

Writers MUST raise the version for every change they publish, and SHOULD follow semantic versioning: the patch number
for corrections, the minor number for additions, the major number for restructuring that changes ids.

### Evolution of the format

Readers reject a higher `formatVersion` and, in version 1, every unknown field. New fields therefore come with a new
format version. New content types do not need one: readers skip types they do not know (section 8).

## 13. Editable packs

Packs that learners make in the app have ids starting with `user.`. Every change in the app publishes the pack again,
and learners can export it as a `.linguapack` file and import it elsewhere. When the app imports a **local file**
whose pack id starts with `user.`, it restores an **editable** pack instead of installing a read-only one. External
editors can use this to hand packs to the app for further editing, and to edit packs exported from the app.

### What the app writes

The [user pack template](templates/user-pack/pack.json) shows a pack exported from the app:

- the id `user.` followed by 16 characters from `a`–`z` and `2`–`7` (80 random bits);
- the version `1.0.<revision>`, where the revision counts the changes;
- a `license` of `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0` or `NONE`;
- flat `sections` with `order` 0, 1, 2…, and section ids of `l` followed by 12 such characters;
- one vocabulary block whose entries have ids of `w` followed by 12 such characters and at most one section each,
  in the order of the lections and then of the words in them;
- pictures at `images/p<12 characters>.webp`;
- no `authors`, `tts`, `audio` or `tts` texts.

### Requirements for an editable import

An import as an editable pack fails with `import.not-editable` unless:

- the pack has at least one vocabulary entry, and no entry id is used twice;
- the title is at most 100 characters;
- every section title is at most 100 characters;
- every entry that has an `image` also has an `imageDescription` (for other packs this is only a warning).

The other rules of this specification apply as for every pack.

### What an editable import keeps

The app keeps the title, the description, the languages, the directions, the sections and the vocabulary entries with
all their text fields and pictures. It drops what the editor cannot edit:

- conjugation blocks and blocks of unknown types;
- `audio` and `tts` of entries, `authors`, `tts.locale` and `minAppFormatVersion`;
- every section of an entry but the first one;
- the nesting of sections: they become flat lections, each parent before its children, ordered by `order` and then by
  their position in the list;
- a license other than the three offered ones.

### Conflicts

- If an editable pack with the same id exists, the learner chooses: **Replace** keeps the ids and so the progress of
  every word; **Keep both** imports the pack under a new id, without progress.
- If a read-only pack with that id is installed, the import gets a new id.
- A pack with a `user.` id from a repository installs read-only, and is refused if an editable pack has the same id
  (`import.user-pack-conflict`). Writers SHOULD NOT list `user.` packs in a repository index.

### Advice for external editors

- To round-trip a pack exported from the app, keep its id, every section and entry id and every picture path, keep the
  version pattern `1.0.<n>` and raise `n` with every change. On Replace, the app's next revision is `n` or its own
  revision plus one, whichever is higher.
- Give new sections and entries ids in the app's style (`l` or `w` and 12 random characters from `a`–`z`, `2`–`7`),
  so they cannot collide with ids the app creates.
- Fields the app drops are lost when the learner next exports the pack from the app. Keep them out of packs meant for
  editing in the app, or warn the user.
- To publish an editable pack for everyone, give it a new id without the `user.` prefix and a version of its own.
  Progress made under the `user.` id does not carry over.

## 14. Validation

### Issues

Readers report each problem as an issue with:

- a **severity**: error or warning;
- a **code**, such as `manifest.invalid-id`;
- a **path** to the value, written `<file>:<JSON path>`, such as `pack.json:$.content[0].entries[2].term`;
- a **message** in English, for logs and developers.

Codes are stable: a code is never renamed or reused for a different problem. An app shows a translated text for each
code it knows and falls back to the message for codes it does not know. The [issue codes](issue-codes.md) document
lists all of them.

A pack with an error is rejected and nothing changes. A pack with warnings only is installed. The app's command-line
validator has a strict mode that treats warnings as errors; the packs the app ships pass it.

### Stages

Readers validate in stages. Some stages stop the validation when they find an error, so fixing one problem can reveal
the next:

1. **Archive**: extraction (section 3). The first problem stops the import.
2. **Files**: the set of files (section 4). Validation continues.
3. **Syntax**: `pack.json` is read, normalized and decoded (section 5). A syntax or schema error in it stops here.
4. **Manifest and sections** (sections 6 and 7). Any error here stops before the content is checked.
5. **Content**: included files and each content block, by its type (sections 8 to 10). A block that cannot be
   decoded is skipped; the others are still checked.
6. **Referenced files**: pictures and recordings of the blocks that could be decoded (section 11).
7. **Installation**: ids across blocks (section 8), and the app's own checks (versions, editable packs, downloads).

### What the schema does not check

The JSON Schema describes the structure: fields, types, required fields, patterns and allowed values. A writer MUST
also check what it cannot express:

- uniqueness of ids, within blocks and across blocks of a type;
- references: `parentId`, `sectionIds`, `tenseId`, `personId`, and cycles of sections;
- different source and target languages, and the speech locale's language;
- NFC normalization, the string length after it (JSON Schema counts code points, not UTF-16 units), control
  characters and blank values;
- every file rule: allowed files, sizes, paths, signatures, picture headers;
- every archive rule.

The [implementers' guide](implementers-guide.md) has a checklist of these rules.

## 15. Repository index

Packs can be offered for download from a GitHub repository. The learner adds the repository as a source (owner,
repository, branch and an optional folder), and the app reads `lingua-index.json` from that folder through the GitHub
contents API. It refreshes the index once a day and offers updates when the index lists a higher version of an
installed pack.

```json
{
    "indexVersion": 1,
    "packs": [
        {
            "id": "org.example.en-es.minimal",
            "path": "packs/minimal-vocabulary.linguapack",
            "version": "1.0.0",
            "formatVersion": 1,
            "sha256": "<64 hex digits>",
            "sourceLanguage": "en",
            "targetLanguage": "es",
            "contentTypes": ["vocabulary"],
            "title": "Spanish: first words",
            "sizeBytes": 451
        }
    ]
}
```

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `indexVersion` | integer | yes | `1` (`index.unsupported-version`) |
| `packs` | array | yes | At most 1,000 entries (`index.too-many-packs`) |
| `id` | string | yes | The pack's id; id pattern, at most 100 characters (`index.invalid-id`) |
| `path` | string | yes | Path of the archive relative to the index's folder: segments of `A`–`Z`, `a`–`z`, `0`–`9`, `.`, `_`, `-`, ending in `.linguapack` (`index.unsafe-path`, `index.invalid-extension`) |
| `version` | string | yes | The pack's version (`index.invalid-version`) |
| `formatVersion` | integer | yes | The pack's format version, 1 (`index.unsupported-format`) |
| `sha256` | string | yes | SHA-256 of the archive file, 64 hex digits (`index.invalid-sha256`) |
| `sourceLanguage` | string | yes | The pack's source language (`index.invalid-language`) |
| `targetLanguage` | string | yes | The pack's target language (`index.invalid-language`) |
| `contentTypes` | array of strings | yes | The content types the pack uses, at least one; ids of at most 50 characters (`index.no-content-types`, `index.invalid-content-type`) |
| `title` | string | yes | The pack's title: not blank, at most 200 characters, no control characters except line feeds (`index.invalid-title`) |
| `description` | string | no | At most 1,000 characters, no control characters except line feeds (`index.invalid-description`) |
| `sizeBytes` | integer | yes | Exact size of the archive file, 1 byte to 100 MiB (`index.invalid-size`) |

Rules:

- The file MUST be at most 1 MiB (`index.too-large`) and valid JSON with all required fields of the right types
  (`index.syntax`). These problems reject the whole index.
- An entry that breaks one of the other rules is skipped with a warning; the others stay available. An id listed twice
  keeps its first entry (`index.duplicate-id`).
- Readers ignore unknown fields in the index, unlike in packs.
- After the download the app checks the size (`download.size-mismatch`) and the checksum
  (`download.sha256-mismatch`), and that the pack's id and version are those of the index entry
  (`download.index-mismatch`). Then the pack goes through the same import as a file.
- Writers SHOULD sort the entries by id and SHOULD generate the index from the final archives, so the checksums and
  sizes are right. The [template index](templates/lingua-index.json) lists the template archives.

## 16. Security considerations

Packs come from anyone. Readers MUST treat every pack and every index as untrusted input:

- Extract archives only into a fresh, empty folder; reject unsafe paths before writing anything, and check after
  resolving each path that it is still inside that folder.
- Count extracted bytes while extracting, and stop at the size and ratio limits. Never trust the sizes an archive
  declares.
- Never follow symbolic links, and never let a referenced path leave the pack.
- Check picture headers before decoding pictures, so oversized or animated images are never decoded.
- Parse JSON strictly, with size limits before parsing.
- Treat the index checksum as protection against corrupt or swapped downloads, not as proof of who made the pack:
  whoever controls the repository controls both the index and the archives.

Writers SHOULD keep personal data out of packs: strip metadata such as camera data, locations or text chunks from
pictures, and do not write user names or file system paths into packs. Text such as bidirectional control characters
(U+202A–U+202E, U+2066–U+2069) is not rejected by readers, but it can make text display misleadingly; writers SHOULD
NOT write it.

Packs often reproduce material from textbooks. Writers SHOULD remind their users that a pack they share must respect
the rights to that material, and SHOULD ask for a license when a pack is created.

## 17. Appendix

### Limits

| Limit | Value |
| --- | --- |
| Entries in an archive, files in a pack | 10,000 |
| Uncompressed size of a pack | 100 MiB |
| Compression ratio (checked after the first MiB) | 100 |
| `pack.json`, each included file | 5 MiB |
| Picture | 1 MiB, 2,048 × 2,048 pixels |
| String (any JSON string) | 1,000 characters |
| Id (pack, section, item, person, tense) | 100 characters |
| Path | 255 characters |
| Repository index | 1 MiB, 1,000 packs |
| Index title | 200 characters |
| Index content type | 50 characters |
| Titles in editable packs (pack and lection) | 100 characters |

### Patterns

```text
Id               ^[a-z0-9]+([._-][a-z0-9]+)*$
Version          ^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$
Language tag     ^[a-zA-Z]{2,3}(-[a-zA-Z]{4})?(-([a-zA-Z]{2}|[0-9]{3}))?$
Index path       ^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*\.linguapack$
SHA-256          ^[0-9a-fA-F]{64}$
Editable pack id ^user\.[a-z2-7]{16}$   (as the app makes them; any user. id is editable)
```

### Templates

| Template | Shows |
| --- | --- |
| [minimal-vocabulary](templates/minimal-vocabulary/pack.json) | The smallest useful pack: one section, three words |
| [vocabulary-lections-media](templates/vocabulary-lections-media/pack.json) | Nested sections, pictures with descriptions, examples, gender, plural, hints, speech text |
| [conjugation](templates/conjugation/pack.json) | Persons, two tenses, a regular and an irregular verb |
| [mixed-with-includes](templates/mixed-with-includes/pack.json) | Both content types in included files, one direction, documentation files |
| [user-pack](templates/user-pack/pack.json) | A pack as the app exports it, which imports as an editable pack |
| [lingua-index.json](templates/lingua-index.json) | A repository index listing the template archives |

Each template folder has a built archive next to it, such as `templates/minimal-vocabulary.linguapack`.

### Changes

| Revision | Date | Changes |
| --- | --- | --- |
| 1.0 | 2026-10-26 | First publication, describing format version 1 as read by wörds 0.11.1 |
