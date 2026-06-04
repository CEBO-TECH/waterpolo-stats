"""Tests for YouTubeService — timestamp calculation and video URLs."""

from datetime import datetime

from src.domain.models import Event, YouTubeStream
from src.domain.services import YouTubeService


class TestYouTubeService:
    svc = YouTubeService()

    def _make_stream(self, start: str = "2026-01-15T18:00:00") -> YouTubeStream:
        return YouTubeStream(
            id="yt1", match_id="m1",
            youtube_url="https://www.youtube.com/watch?v=abc123",
            video_id="abc123",
            stream_start_time=datetime.fromisoformat(start),
        )

    def _make_event(self, timestamp: str = "2026-01-15T18:05:00") -> Event:
        return Event(
            id="e1", club_id="c1", match_id="m1",
            player_id="p1", player_name="Jan",
            timestamp=datetime.fromisoformat(timestamp),
        )

    def test_seek_position_with_rewind(self):
        """Event at 5 min, rewind 30s → seek to 4:30 (270s)."""
        pos = self.svc.calculate_seek_position(
            stream_start=datetime.fromisoformat("2026-01-15T18:00:00"),
            event_time=datetime.fromisoformat("2026-01-15T18:05:00"),
        )
        assert pos == 270  # 300 - 30

    def test_seek_position_near_start(self):
        """Event at 20s, rewind 30s → clamp to 0."""
        pos = self.svc.calculate_seek_position(
            stream_start=datetime.fromisoformat("2026-01-15T18:00:00"),
            event_time=datetime.fromisoformat("2026-01-15T18:00:20"),
        )
        assert pos == 0  # 20 - 30 = -10, clamped to 0

    def test_video_url_generation(self):
        stream = self._make_stream()
        event = self._make_event("2026-01-15T18:05:00")
        url = self.svc.get_event_video_url(event, stream)
        assert url == "https://www.youtube.com/watch?v=abc123&t=270s"

    def test_video_url_none_without_stream_start(self):
        stream = YouTubeStream(
            id="yt1", match_id="m1",
            youtube_url="https://youtube.com/watch?v=abc",
            video_id="abc",
            stream_start_time=None,
        )
        event = self._make_event()
        assert self.svc.get_event_video_url(event, stream) is None

    def test_sync_offline_timestamps(self):
        stream = self._make_stream("2026-01-15T18:00:00")
        events = [
            Event(
                id="e1", club_id="c1", match_id="m1",
                player_id="p1", player_name="Jan",
                timestamp=datetime.fromisoformat("2026-01-15T18:03:00"),
                video_timestamp=None,  # Offline — no timestamp yet
            ),
            Event(
                id="e2", club_id="c1", match_id="m1",
                player_id="p1", player_name="Jan",
                timestamp=datetime.fromisoformat("2026-01-15T18:10:00"),
                video_timestamp=None,
            ),
        ]

        synced = self.svc.sync_offline_timestamps(events, stream)
        assert synced[0].video_timestamp == 150  # 180 - 30
        assert synced[1].video_timestamp == 570  # 600 - 30
