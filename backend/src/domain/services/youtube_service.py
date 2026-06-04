"""YouTube stream integration — timestamps, video links, offline sync.

New service from roadmapa Faza 1: integracja z transmisją YouTube.
"""

from datetime import datetime

from src.domain.models import Event, YouTubeStream


class YouTubeService:
    # Actions last max 28 seconds, rewind 30s to show full action
    DEFAULT_REWIND_SECONDS = 30

    def get_event_video_url(
        self, event: Event, stream: YouTubeStream
    ) -> str | None:
        """Generate a YouTube URL that seeks to the moment of an event.

        The URL is rewound by DEFAULT_REWIND_SECONDS to show the full action.
        Returns None if stream has no start time or event has no timestamp.
        """
        if not stream.stream_start_time or not event.timestamp:
            return None

        seek_seconds = self.calculate_seek_position(
            stream.stream_start_time, event.timestamp
        )
        if seek_seconds < 0:
            seek_seconds = 0

        return f"https://www.youtube.com/watch?v={stream.video_id}&t={seek_seconds}s"

    def calculate_seek_position(
        self,
        stream_start: datetime,
        event_time: datetime,
        rewind_seconds: int | None = None,
    ) -> int:
        """Calculate video seek position in seconds.

        video_position = (event_time - stream_start) - rewind
        """
        if rewind_seconds is None:
            rewind_seconds = self.DEFAULT_REWIND_SECONDS

        delta = (event_time - stream_start).total_seconds()
        return max(0, int(delta - rewind_seconds))

    def sync_offline_timestamps(
        self, events: list[Event], stream: YouTubeStream
    ) -> list[Event]:
        """Recalculate video_timestamp for events that were recorded offline.

        When offline, events store device clock time. After reconnection,
        this method recalculates video timestamps based on the stream start time.
        """
        if not stream.stream_start_time:
            return events

        for event in events:
            if event.timestamp and event.video_timestamp is None:
                event.video_timestamp = self.calculate_seek_position(
                    stream.stream_start_time, event.timestamp
                )

        return events
