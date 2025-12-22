# Album Artist Website Plugin for MusicBrainz Picard

A plugin for [MusicBrainz Picard](https://picard.musicbrainz.org/) that automatically adds album artist(s) official homepage(s) from the MusicBrainz database to your music files.

- Plugin name: Album Artist Website
- Plugin version: 2.0.1
- Picard plugin API: 3.0

## Description

This plugin retrieves the official homepage URLs for album artists from MusicBrainz and adds them to the `website` tag of your music files. It queries the MusicBrainz database for artist information and extracts any "official homepage" relationships that are not marked as ended.

## Features

- Automatically fetches official artist homepages from MusicBrainz
- Caches artist website information to minimize API requests
- Handles multiple album artists
- Non-blocking: uses Picard's async webservice infrastructure
- Supports multi-valued website tags (sorts alphabetically)

## Installation

1. Download this repository (or a release zip).
2. Copy this plugin folder to your Picard plugins directory (it must contain `__init__.py` and `MANIFEST.toml`):
   - **Windows**: `%APPDATA%\MusicBrainz\Picard\plugins3\`
   - **macOS**: `~/.config/MusicBrainz/Picard/plugins3/`
   - **Linux**: `~/.config/MusicBrainz/Picard/plugins3/`
3. Restart Picard
4. Enable the plugin in **Options → Plugins**

## Supported Picard Versions

This plugin is compatible with:

- **Picard 3.0** and later
- **Plugin API version**: 3.0

⚠️ **Note**: This is a Picard 3.x plugin and will NOT work with Picard 2.x. For Picard 2.x, use the original plugin from the [official plugins repository](https://github.com/metabrainz/picard-plugins).

## Usage

Once installed and enabled:

1. Load files into Picard
2. Lookup and match your files to MusicBrainz releases
3. The plugin automatically fetches artist websites during metadata processing
4. Save your files - the `website` tag will contain the artist's official homepage(s)

### Tag Information

- **Tag name**: `website`
- **Content**: URL(s) of the album artist's official homepage(s) as defined in MusicBrainz
- **Multi-value**: Yes - if an artist has multiple official homepages, they will all be added (sorted alphabetically)
- **Scope**: Per-track (applied to all tracks from the same album artist)

## Behavior Notes

### Multiple Album Artists

When an album has multiple album artists, the plugin will fetch and merge the official homepages for all artists into the `website` tag.

### Caching

The plugin maintains an in-memory cache of artist websites keyed by MusicBrainz artist ID (MBID). This prevents redundant API calls when processing multiple albums by the same artist in a single Picard session.

### Ended Relationships

The plugin filters out any artist homepage relationships that are marked as "ended" in MusicBrainz, ensuring only current/active websites are added.

### Non-blocking Operation

All MusicBrainz webservice queries are performed asynchronously using Picard's album task API, so the UI remains responsive during metadata fetching.

## Credits

**Original Authors**:

- Sophist
- Sambhav Kothari
- Philipp Wolfer

**Picard 3.x Port**: frcooper

This is a port of the original "Album Artist Website" plugin from the official [picard-plugins](https://github.com/metabrainz/picard-plugins) repository (branch 2.0) to support Picard 3.x with the new plugin API.

## License

GPL-2.0-or-later

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

## Links

- [MusicBrainz Picard](https://picard.musicbrainz.org/)
- [Picard Plugins Documentation](https://picard-docs.musicbrainz.org/en/extending/plugins.html)
- [Original Plugin Repository](https://github.com/metabrainz/picard-plugins)

## Development

### Shared environment

These plugins are intended to be developed using the same Python environment as Picard itself.

- Create Picard's venv in the Picard repo (recommended path: `../picard/.venv`).
- This repo's VS Code settings point at that interpreter and add `f:/repos/picard` to analysis paths.

### Running tests

- `python -m unittest discover -s tests -p "test*.py" -v`

This plugin uses Picard 3.x's plugin API with the following key components:

### Plugin Structure

- **MANIFEST.toml**: Contains plugin metadata (name, version, authors, API versions, etc.)
- ****init**.py**: Main plugin code with `enable()` and `disable()` entry points

### Implementation Details

The plugin:

1. Registers a track metadata processor via `api.register_track_metadata_processor()`
2. Extracts `musicbrainz_albumartistid` from track metadata
3. Checks an in-memory cache for known artist websites
4. For uncached artists, creates album tasks using `api.add_album_task()` with webservice requests
5. Parses XML responses to extract "official homepage" URL relationships
6. Updates track and file metadata with retrieved website URLs
7. Completes album tasks via `api.complete_album_task()`

The implementation uses Python's `threading.Lock` for thread-safe queue management and coordinates with Picard's album loading system through the task API.

## Releasing

This repository uses tags to publish releases. Creating a tag `vX.Y.Z` triggers a GitHub Action that creates a GitHub Release with notes listing all commits since the previous tag.

To bump the version (updates `MANIFEST.toml` and this README), commit, tag, and push:

- `python scripts/bump_version.py --bump patch`

Or set an explicit version:

- `python scripts/bump_version.py --new-version 2.0.0`
