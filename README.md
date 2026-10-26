# wörds

wörds is a flashcard app for learning languages: vocabulary and verb forms, with spaced repetition, offline.

wörds ist eine Lernkarten-App zum Sprachenlernen: Vokabeln und Verbformen, mit verteilter Wiederholung, offline.

| | English | Deutsch |
| --- | --- | --- |
| **Using the app (latest version)** · **Die App benutzen (aktuelle Version)** | [User guide](en/user-guide.md) | [Benutzerhandbuch](de/benutzerhandbuch.md) |
| **Privacy** · **Datenschutz** | [Privacy policy](en/privacy-policy.md) | [Datenschutzerklärung](de/datenschutz.md) |
| **Earlier versions** · **Frühere Versionen** | [User guide 0.11.0](versions/0.11.0/en/user-guide.md) | [Benutzerhandbuch 0.11.0](versions/0.11.0/de/benutzerhandbuch.md) |
| | [User guide 0.10.0](versions/0.10.0/en/user-guide.md) | [Benutzerhandbuch 0.10.0](versions/0.10.0/de/benutzerhandbuch.md) |
| | [User guide 0.9.0](versions/0.9.0/en/user-guide.md) | [Benutzerhandbuch 0.9.0](versions/0.9.0/de/benutzerhandbuch.md) |

## Versions

The user guide describes one version of the app; the privacy policy applies to all of them. `en/` and `de/` hold the
guide of the latest version, so its address never changes. Earlier versions are kept, with their screenshots, in
`versions/<version>/` and listed in `versions.json`. Before changing the guide for a new version, for example 0.11.0:

1. `python3 tools/docs/build-manual.py --freeze 0.11.0` copies the current guides and their images to
   `versions/<latest>/`, lists that version as earlier, and makes 0.11.0 the latest (in `versions.json` and in the
   sentence of both guides that names the version).
2. Link the frozen version in `index.html` and in the table above.
3. Update the guides and run `python3 tools/docs/build-manual.py`.

`--check` (run by CI) fails when an HTML page is out of date, a guide names a different version than
`versions.json`, or `index.html` does not link an earlier version.
