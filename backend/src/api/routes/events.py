"""Event routes — port of /api/events and related endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.api.deps import AnyMember, CoachOrOwner, EventRepo, SettingsRepo
from src.api.schemas.common import OkCountResponse, OkResponse
from src.api.schemas.event import EventBatchCreate, EventResponse, UndoRequest
from src.domain.models import EVENT_FLAG_FIELDS, Event
from src.domain.services import EventService

router = APIRouter(prefix="/v1/clubs/{club_id}", tags=["events"])
event_service = EventService()


@router.post("/events", response_model=OkCountResponse)
async def create_events(
    club_id: str, body: EventBatchCreate,
    ctx: CoachOrOwner, event_repo: EventRepo, settings_repo: SettingsRepo,
):
    """Batch insert events. Port of POST /api/events."""
    settings = await settings_repo.get_for_club(club_id)

    events = []
    for ev_data in body.events:
        match_id = ev_data.match_id or settings.active_match
        quarter = ev_data.quarter or settings.quarter

        kwargs = {
            "id": str(uuid.uuid4()),
            "club_id": club_id,
            "match_id": match_id,
            "player_id": ev_data.player_id,
            "player_name": ev_data.player_name,
            "quarter": quarter,
            "team": ev_data.team,
            "event_type": ev_data.event_type,
            "subtype": ev_data.subtype,
            "value": ev_data.value,
            "note": ev_data.note,
        }
        for flag in EVENT_FLAG_FIELDS:
            kwargs[flag] = getattr(ev_data, flag, 0)

        # Optional explicit event time (for backfilling historical matches so the
        # YouTube replay seek is correct); otherwise the model defaults to "now".
        if ev_data.timestamp:
            try:
                kwargs["timestamp"] = datetime.fromisoformat(ev_data.timestamp)
            except ValueError:
                pass

        events.append(Event(**kwargs))

    count = await event_repo.create_batch(events)
    return OkCountResponse(count=count)


@router.get("/matches/{match_id}/events", response_model=list[EventResponse])
async def get_match_events(
    club_id: str, match_id: str,
    ctx: AnyMember, repo: EventRepo,
    limit: int = Query(default=20),
):
    """Get recent events for a match. Port of GET /api/events/[matchId]."""
    events = await repo.get_recent(club_id, match_id, limit)
    return [
        EventResponse(
            id=ev.id,
            timestamp=ev.timestamp.isoformat(),
            quarter=ev.quarter,
            player_name=ev.player_name,
            event_type=ev.event_type,
            note=ev.note,
            action=event_service.get_event_action(ev),
        )
        for ev in events
    ]


@router.delete("/events/{event_id}", response_model=OkResponse)
async def delete_event(
    club_id: str, event_id: str, ctx: CoachOrOwner, repo: EventRepo,
):
    """Delete a specific event. Port of DELETE /api/events/delete."""
    try:
        await repo.delete_by_id(club_id, event_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Event not found")
    return OkResponse()


@router.post("/events/undo")
async def undo_last_event(
    club_id: str, body: UndoRequest,
    ctx: CoachOrOwner, event_repo: EventRepo, settings_repo: SettingsRepo,
):
    """Undo the last event within a time window. Port of POST /api/events/undo."""
    settings = await settings_repo.get_for_club(club_id)
    if not settings.active_match:
        return {"ok": False, "reason": "No active match"}

    deleted = await event_repo.delete_last_within_window(
        club_id, settings.active_match, body.window_minutes
    )
    if deleted:
        return {"ok": True}
    return {"ok": False, "reason": "No recent event found within time window"}
