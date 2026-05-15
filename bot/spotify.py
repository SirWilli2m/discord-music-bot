from __future__ import annotations

import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from bot.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

SPOTIFY_URL_PATTERN = re.compile(
    r"https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)"
)


class SpotifyClient:
    def __init__(self) -> None:
        self.enabled = bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)
        self.client: spotipy.Spotify | None = None
        if self.enabled:
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
            )
            self.client = spotipy.Spotify(auth_manager=auth_manager)

    @staticmethod
    def is_spotify_url(url: str) -> bool:
        return bool(SPOTIFY_URL_PATTERN.match(url))

    @staticmethod
    def parse_url(url: str) -> tuple[str, str] | None:
        match = SPOTIFY_URL_PATTERN.match(url)
        if match:
            return match.group(1), match.group(2)
        return None

    def get_track_query(self, track: dict) -> str:
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        name = track.get("name", "")
        return f"{artists} - {name}"

    def get_tracks_from_url(self, url: str) -> list[str]:
        if not self.enabled or not self.client:
            return []

        parsed = self.parse_url(url)
        if not parsed:
            return []

        resource_type, resource_id = parsed
        queries: list[str] = []

        if resource_type == "track":
            track = self.client.track(resource_id)
            if track:
                queries.append(self.get_track_query(track))

        elif resource_type == "album":
            album = self.client.album(resource_id)
            if album and album.get("tracks"):
                for track in album["tracks"]["items"]:
                    queries.append(self.get_track_query(track))

        elif resource_type == "playlist":
            results = self.client.playlist_tracks(resource_id)
            if results:
                for item in results["items"]:
                    track = item.get("track")
                    if track:
                        queries.append(self.get_track_query(track))
                while results and results.get("next"):
                    results = self.client.next(results)
                    if results:
                        for item in results["items"]:
                            track = item.get("track")
                            if track:
                                queries.append(self.get_track_query(track))

        return queries
