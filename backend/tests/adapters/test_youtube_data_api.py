"""Unit tests for the YouTube Data API adapter (no network)."""

import pytest

from src.adapters.youtube.data_api import YouTubeDataApiAdapter


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/not-a-video", None),
        ("", None),
    ],
)
def test_extract_video_id(url, expected):
    assert YouTubeDataApiAdapter(api_key="").extract_video_id(url) == expected


@pytest.mark.asyncio
async def test_start_time_none_without_key():
    # No API key → no network call, returns None (caller keeps manual fallback).
    adapter = YouTubeDataApiAdapter(api_key="")
    assert await adapter.get_stream_start_time("dQw4w9WgXcQ") is None
