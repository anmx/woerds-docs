# wörds

wörds is a flashcard app for learning languages: vocabulary and verb forms, with spaced repetition, offline.

wörds ist eine Lernkarten-App zum Sprachenlernen: Vokabeln und Verbformen, mit verteilter Wiederholung, offline.

| | English | Deutsch |
| --- | --- | --- |
| **Using the app (latest version)** · **Die App benutzen (aktuelle Version)** | [User guide](en/user-guide.md) | [Benutzerhandbuch](de/benutzerhandbuch.md) |
| **Privacy** · **Datenschutz** | [Privacy policy](en/privacy-policy.md) | [Datenschutzerklärung](de/datenschutz.md) |
| **Making language packs** · **Sprachpakete erstellen** | [Language pack specification](spec/README.md) (for developers) | [Sprachpaket-Spezifikation](spec/README.md) (für die Entwicklung, auf Englisch) |
| **Earlier versions** · **Frühere Versionen** | [User guide 0.20.1](versions/0.20.1/en/user-guide.md)<br>[User guide 0.20.0](versions/0.20.0/en/user-guide.md)<br>[User guide 0.19.0](versions/0.19.0/en/user-guide.md)<br>[User guide 0.18.2](versions/0.18.2/en/user-guide.md)<br>[User guide 0.18.1](versions/0.18.1/en/user-guide.md)<br>[User guide 0.18.0](versions/0.18.0/en/user-guide.md)<br>[User guide 0.17.0](versions/0.17.0/en/user-guide.md)<br>[User guide 0.16.0](versions/0.16.0/en/user-guide.md) | [Benutzerhandbuch 0.20.1](versions/0.20.1/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.20.0](versions/0.20.0/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.19.0](versions/0.19.0/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.18.2](versions/0.18.2/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.18.1](versions/0.18.1/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.18.0](versions/0.18.0/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.17.0](versions/0.17.0/de/benutzerhandbuch.md)<br>[Benutzerhandbuch 0.16.0](versions/0.16.0/de/benutzerhandbuch.md) |
| | [User guide 0.15.0](versions/0.15.0/en/user-guide.md) | [Benutzerhandbuch 0.15.0](versions/0.15.0/de/benutzerhandbuch.md) |
| | [User guide 0.14.0](versions/0.14.0/en/user-guide.md) | [Benutzerhandbuch 0.14.0](versions/0.14.0/de/benutzerhandbuch.md) |
| | [User guide 0.13.0](versions/0.13.0/en/user-guide.md) | [Benutzerhandbuch 0.13.0](versions/0.13.0/de/benutzerhandbuch.md) |
| | [User guide 0.12.0](versions/0.12.0/en/user-guide.md) | [Benutzerhandbuch 0.12.0](versions/0.12.0/de/benutzerhandbuch.md) |
| | [User guide 0.11.1](versions/0.11.1/en/user-guide.md) | [Benutzerhandbuch 0.11.1](versions/0.11.1/de/benutzerhandbuch.md) |
| | [User guide 0.11.0](versions/0.11.0/en/user-guide.md) | [Benutzerhandbuch 0.11.0](versions/0.11.0/de/benutzerhandbuch.md) |
| | [User guide 0.10.0](versions/0.10.0/en/user-guide.md) | [Benutzerhandbuch 0.10.0](versions/0.10.0/de/benutzerhandbuch.md) |
| | [User guide 0.9.0](versions/0.9.0/en/user-guide.md) | [Benutzerhandbuch 0.9.0](versions/0.9.0/de/benutzerhandbuch.md) |

## About this project · Über dieses Projekt

wörds is an open-source hobby project under the Apache License 2.0. It is provided without warranty: there is no promise that the app is free of
errors, secure or will stay available, and its security has not been independently reviewed, including the exchange
of packs nearby. Using it, and the risks that come with that, are solely your responsibility; this includes packs you
accept from files, from GitHub or from other people. Rights that cannot be excluded by law are not affected.

wörds ist ein Hobbyprojekt mit offenem Quellcode unter der Apache-Lizenz 2.0. Es wird ohne Gewähr angeboten: Es gibt keine Zusage, dass die App
fehlerfrei, sicher oder dauerhaft verfügbar ist, und ihre Sicherheit wurde nicht unabhängig geprüft, auch nicht der
Austausch von Paketen in der Nähe. Die Nutzung und die damit verbundenen Risiken liegen in deiner alleinigen
Verantwortung; das gilt auch für Pakete, die du aus Dateien, von GitHub oder von anderen Personen annimmst. Rechte,
die gesetzlich nicht ausgeschlossen werden können, bleiben unberührt.

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

## Language pack specification

`spec/` holds the specification of the language pack format for developers of other tools (English only). It is
versioned by the pack format (`spec/v1/`), not by the app, so `--freeze` leaves it alone. Its Markdown pages are built
with the guides; the template archives, the conformance archives and the template index are built by
`python3 tools/spec/build-spec.py` (CI runs it with `--check`). See [spec/README.md](spec/README.md).
