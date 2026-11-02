# wörds

wörds is a flashcard app for learning languages: vocabulary and verb forms, with spaced repetition, offline.

wörds ist eine Lernkarten-App zum Sprachenlernen: Vokabeln und Verbformen, mit verteilter Wiederholung, offline.

The documentation is published at <https://anmx.github.io/woerds-docs/>.

| | English | Deutsch |
| --- | --- | --- |
| **Using the app** · **Die App benutzen** | [User guide](https://anmx.github.io/woerds-docs/en/user-guide) | [Benutzerhandbuch](https://anmx.github.io/woerds-docs/de/user-guide) |
| **Privacy** · **Datenschutz** | [Privacy policy](https://anmx.github.io/woerds-docs/en/privacy-policy) | [Datenschutzerklärung](https://anmx.github.io/woerds-docs/de/privacy-policy) |
| **Making language packs** · **Sprachpakete erstellen** | [Language pack specification](https://anmx.github.io/woerds-docs/en/spec) (for developers) | [Sprachpaket-Spezifikation](https://anmx.github.io/woerds-docs/en/spec) (für die Entwicklung, auf Englisch) |

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

## Building the site

The site is built with [Nextra](https://nextra.site) from the Markdown in `content/`. GitHub Actions does the work in a
container: `.github/workflows/ci.yml` checks every pull request, and `.github/workflows/deploy.yml` builds `main` and
publishes it to GitHub Pages. No generated file is committed.

To try it before pushing, run the same image locally:

```sh
docker run --rm -p 3000:3000 -v "$PWD":/w -w /w -v woerds_nm:/w/node_modules node:24 sh -c 'npm ci && npm run dev -- -H 0.0.0.0'
```

## Versions

The site shows the guide of the latest version only. For a new version, update both guides, including the sentence that
names the version (`site.py check` fails when they differ); merging to `main` publishes them. Earlier guides remain in
the git history.

## Language pack specification

The pages of the specification (English only) are in `content/en/spec/`. `spec/` holds its schemas, templates and
conformance cases, which are served at their addresses under `spec/v1/`. It is versioned by the pack format (`v1`), not
by the app. The template archives, the conformance archives and the template index are built by
`python3 tools/spec/build-spec.py` (CI runs it with `--check`).
