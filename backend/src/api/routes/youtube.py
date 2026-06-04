"""YouTube stream routes."""

import re
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.deps import AnyMember, CoachOrOwner, EventRepo, YouTubeRepo
from src.domain.models import YouTubeStream
from src.domain.services import YouTubeService

router = APIRouter(prefix="/v1/clubs/{club_id}/matches/{match_id}", tags=["youtube"])
youtube_service = YouTubeService()


class YouTubeStreamCreate(BaseModel):
    youtube_url: str
    stream_start_time: str | None = None  # ISO datetime


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@router.post("/youtube", status_code=201)
async def attach_youtube_stream(
    club_id: str, match_id: str,
    body: YouTubeStreamCreate,
    ctx: CoachOrOwner,
    repo: YouTubeRepo,
):
    video_id = _extract_video_id(body.youtube_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    start_time = None
    if body.stream_start_time:
        start_time = datetime.fromisoformat(body.stream_start_time)

    # Upsert
    existing = await repo.get_for_match(match_id)
    if existing:
        existing.youtube_url = body.youtube_url
        existing.video_id = video_id
        existing.stream_start_time = start_time
        updated = await repo.update(existing)
        return {
            "youtube_url": updated.youtube_url,
            "video_id": updated.video_id,
            "stream_start_time": updated.stream_start_time.isoformat() if updated.stream_start_time else None,
        }

    stream = YouTubeStream(
        id=str(uuid.uuid4()),
        match_id=match_id,
        youtube_url=body.youtube_url,
        video_id=video_id,
        stream_start_time=start_time,
    )
    created = await repo.create(stream)
    return {
        "youtube_url": created.youtube_url,
        "video_id": created.video_id,
        "stream_start_time": created.stream_start_time.isoformat() if created.stream_start_time else None,
    }


@router.get("/youtube")
async def get_youtube_stream(
    club_id: str, match_id: str, ctx: AnyMember, repo: YouTubeRepo,
):
    stream = await repo.get_for_match(match_id)
    if not stream:
        raise HTTPException(status_code=404, detail="No YouTube stream for this match")
    return {
        "youtube_url": stream.youtube_url,
        "video_id": stream.video_id,
        "stream_start_time": stream.stream_start_time.isoformat() if stream.stream_start_time else None,
    }


@router.get("/events/{event_id}/video-url")
async def get_event_video_url(
    club_id: str, match_id: str, event_id: str,
    ctx: AnyMember,
    youtube_repo: YouTubeRepo,
    event_repo: EventRepo,
):
    """Get a YouTube URL that seeks to the moment of an event (rewound by 30s)."""
    stream = await youtube_repo.get_for_match(match_id)
    if not stream:
        raise HTTPException(status_code=404, detail="No YouTube stream")

    events = await event_repo.get_recent(club_id, match_id, limit=1000)
    event = next((e for e in events if e.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    url = youtube_service.get_event_video_url(event, stream)
    if not url:
        raise HTTPException(status_code=400, detail="Cannot calculate video timestamp")

    return {"video_url": url}
