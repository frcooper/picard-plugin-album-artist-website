# -*- coding: utf-8 -*-
#
# Album Artist Website Plugin for MusicBrainz Picard 3.x
#
# Copyright (C) 2007-2024 Sophist, Sambhav Kothari, Philipp Wolfer
# Copyright (C) 2024 frcooper (Picard 3.x port)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from functools import partial
from threading import Lock

from picard.plugin3.api import (
    Album,
    Metadata,
    PluginApi,
    Track,
)


class AlbumArtistWebsite:

    class ArtistWebsiteQueue:
        """Thread-safe queue for managing artist website fetch requests."""

        def __init__(self):
            self._lock = Lock()
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            with self._lock:
                return self.queue.get(name)

        def __setitem__(self, name, value):
            with self._lock:
                self.queue[name] = value

        def append(self, name, value):
            with self._lock:
                if name in self.queue:
                    self.queue[name].append(value)
                    return False
                else:
                    self.queue[name] = [value]
                    return True

        def remove(self, name):
            with self._lock:
                return self.queue.pop(name, None)

    def __init__(self, api: PluginApi):
        self.api = api
        self.website_cache = {}
        self.website_queue = self.ArtistWebsiteQueue()

    def add_artist_website(self, api: PluginApi, track: Track, track_metadata: Metadata, track_node: dict, release_node: dict | None):
        """Process track metadata to add artist websites."""
        albumArtistIds = track_metadata.getall('musicbrainz_albumartistid')
        album = track.album
        
        for artistId in albumArtistIds:
            if artistId in self.website_cache:
                if self.website_cache[artistId]:
                    self.add_websites_to_track(track, self.website_cache[artistId])
            else:
                self.website_add_track(album, track, artistId)

    def website_add_track(self, album: Album, track: Track, artistId: str):
        """Queue a track for website fetching and make webservice request if needed."""
        if self.website_queue.append(artistId, (track, album)):
            # This is the first track requesting this artist's website
            path = f"/ws/2/artist/{artistId}"
            queryargs = {"inc": "url-rels"}
            
            task_id = f"artist_website_{artistId}"
            self.api.add_album_task(
                album,
                task_id,
                f"Fetching artist website for {artistId}",
                request_factory=lambda: self.api.web_service.get(
                    "musicbrainz.org",
                    443,
                    path,
                    partial(self.website_process, artistId),
                    parse_response_type="xml",
                    priority=True,
                    important=False,
                    queryargs=queryargs,
                    use_https=True
                )
            )

    def website_process(self, artistId: str, response, reply, error):
        """Process the artist website response from MusicBrainz."""
        if error:
            self.api.logger.error("Network error retrieving artist record for %s: %s", artistId, error)
            tuples = self.website_queue.remove(artistId)
            if tuples:
                for track, album in tuples:
                    self.api.complete_album_task(album, f"artist_website_{artistId}")
            return
            
        urls = self.artist_process_metadata(artistId, response)
        self.website_cache[artistId] = urls
        tuples = self.website_queue.remove(artistId)
        
        if tuples:
            for track, album in tuples:
                self.add_websites_to_track(track, urls)
                self.api.complete_album_task(album, f"artist_website_{artistId}")

    def add_websites_to_track(self, track: Track, urls: list[str]):
        """Add website URLs to track and file metadata."""
        tm = track.metadata
        websites = tm.getall('website')
        websites += urls
        websites.sort()
        tm['website'] = websites
        
        for file in track.iterfiles(True):
            file.metadata['website'] = websites

    def artist_process_metadata(self, artistId: str, response):
        """Extract official homepage URLs from artist metadata response."""
        self.api.logger.debug("Processing artist record for official website urls: %s", artistId)
        relations = self.artist_get_relations(response)
        
        if not relations:
            self.api.logger.info("Artist %s does not have any associated urls", artistId)
            return []

        urls = []
        for relation in relations:
            self.api.logger.debug("Examining relation: %s", relation)
            if 'type' in relation.attribs and relation.type == 'official homepage':
                if 'target' in relation.children and len(relation.target) > 0:
                    if 'ended' not in relation.children or relation.ended[0].text != 'true':
                        url = relation.target[0].text
                        self.api.logger.debug("Adding artist url: %s", url)
                        urls.append(url)
                    else:
                        self.api.logger.debug("Artist url has ended: %s", relation.target[0].text)
                else:
                    self.api.logger.debug("No url in relation: %s", relation)

        if urls:
            self.api.logger.info("Artist %s official homepages: %s", artistId, urls)
        else:
            self.api.logger.info("Artist %s does not have any official website urls", artistId)
        
        return sorted(urls)

    def artist_get_relations(self, response):
        """Extract relation list from artist XML response."""
        self.api.logger.debug("artist_get_relations called")
        
        if 'metadata' in response.children and len(response.metadata) > 0:
            if 'artist' in response.metadata[0].children and len(response.metadata[0].artist) > 0:
                if 'relation_list' in response.metadata[0].artist[0].children and len(response.metadata[0].artist[0].relation_list) > 0:
                    if 'relation' in response.metadata[0].artist[0].relation_list[0].children:
                        relations = response.metadata[0].artist[0].relation_list[0].relation
                        self.api.logger.debug("artist_get_relations returning: %s", relations)
                        return relations
                    else:
                        self.api.logger.debug("artist_get_relations - no relation in relation_list")
                else:
                    self.api.logger.debug("artist_get_relations - no relation_list in artist")
            else:
                self.api.logger.debug("artist_get_relations - no artist in metadata")
        else:
            self.api.logger.debug("artist_get_relations - no metadata in response")
        
        return None


# Plugin entry points for Picard 3.x
_plugin_instance = None


def enable(api: PluginApi) -> None:
    """Enable the plugin and register metadata processor."""
    global _plugin_instance
    _plugin_instance = AlbumArtistWebsite(api)
    api.register_track_metadata_processor(_plugin_instance.add_artist_website)


def disable() -> None:
    """Disable the plugin and clean up."""
    global _plugin_instance
    _plugin_instance = None
