# Copilot instructions for Album Artist Website

Context: This folder contains the `Album Artist Website` plugin (`__init__.py`). It fetches the album artist(s) official homepage URL(s) from MusicBrainz and writes them to the `website` tag.

Key behaviors
- Register a track metadata processor.
- Read album artist MBIDs from `musicbrainz_albumartistid`.
- Fetch artist URL relationships (`inc=url-rels`) via Picard's webservice API (async; must not block UI).
- Filter for relationship type `official homepage` and ignore ended relationships.
- Merge multiple artists' URLs, sort, and write to both track metadata and file metadata.

Implementation notes
- No external dependencies.
- Preserve Picard async task behavior: use `api.add_album_task` and `api.complete_album_task`.
- Keep thread-safety for shared structures (`website_cache`, `website_queue`).

Dev environment invariants (keep these maintained)
- This plugin is developed against a local Picard source checkout at `f:/repos/picard`.
- Use the same Python environment as Picard (the `.venv` inside the Picard repo).
- Import resolution MUST work during development (no suppressing missing-import errors for Picard).
- The repository uses:
  - `pyrightconfig.json` with `extraPaths: ["f:/repos/picard"]`.
  - `.vscode/settings.json` with `python.analysis.extraPaths` pointing at `f:/repos/picard`.
  - A local `.env` (ignored by git) setting `PYTHONPATH=f:/repos/picard`.

Release/versioning rules
- Keep `MANIFEST.toml` and `README.md` plugin version in sync.
- Use tags `vX.Y.Z`; a GitHub Action creates a Release with notes listing commits since the previous tag.
