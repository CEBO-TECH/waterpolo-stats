"""YouTube Data API adapter — URL parsing + live-stream metadata.

The per-event replay feature needs the real wall-clock start of the broadcast
so an event's timestamp maps to the right second in the video. YouTube exposes
this as ``liveStreamingDetails.actualStartTime``; reading it with the Data API
lets the coach just paste the link — no manual "set start" step.

Follows the same graceful-degradation pattern as the Claude NLU adapter: when no
API key is configured (or the HTTP call fails), API-backed methods return None
and callers fall back to whatever they already had.
"""

import re
from datetime import datetime, timezone

from src.config import settings
from src.domain.ports.external import VideoInfo, YouTubePort

# youtu.be/<id>, watch?v=<id>, /embed/<id>, /live/<id>, /v/<id>
_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:embed/|live/)([a-zA-Z0-9_-]{11})"),
]
_VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeDataApiAdapter(YouTubePort):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def extract_video_id(self, url: str) -> str | None:
        for pattern in _ID_PATTERNS:
            match = pattern.search(url or "")
            if match:
                return match.group(1)
        return None

    async def _videos_list(self, video_id: str, part: str) -> dict | None:
        """Return the first ``items[]`` entry from videos.list, or None."""
        if not self._api_key or not video_id:
            return None
        try:
            import httpx  # transitively available via the anthropic SDK
        except ImportError:
            return None
        params = {"part": part, "id": video_id, "key": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(_VIDEOS_ENDPOINT, params=params)
            if resp.status_code != 200:
                return None
            items = resp.json().get("items") or []
            return items[0] if items else None
        except Exception:
            return None

    async def get_stream_start_time(self, video_id: str) -> datetime | None:
        item = await self._videos_list(video_id, "liveStreamingDetails")
        if not item:
            return None
        details = item.get("liveStreamingDetails") or {}
        # actualStartTime is set once the broadcast goes live; fall back to the
        # scheduled time so a not-yet-started stream still anchors sensibly.
        raw = details.get("actualStartTime") or details.get("scheduledStartTime")
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        # Store as naive UTC to match event timestamps (datetime.utcnow()).
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    async def get_video_info(self, url: str) -> VideoInfo | None:
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        item = await self._videos_list(video_id, "snippet")
        if not item:
            return None
        title = (item.get("snippet") or {}).get("title", "")
        return VideoInfo(video_id=video_id, title=title)

    def calculate_video_timestamp(
        self, stream_start: datetime, event_time: datetime, rewind_seconds: int = 30
    ) -> int:
        delta = (event_time - stream_start).total_seconds()
        return max(0, int(delta - rewind_seconds))


def get_youtube_port() -> YouTubeDataApiAdapter:
    """Adapter for YouTube URL parsing + live-stream metadata.

    Always returns an instance (URL parsing works offline); API-backed calls
    degrade to None when ``YOUTUBE_API_KEY`` is unset.
    """
    return YouTubeDataApiAdapter(api_key=settings.YOUTUBE_API_KEY)
