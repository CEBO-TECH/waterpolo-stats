import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import EVENT_FLAG_FIELDS, Event
from src.domain.ports.repositories import EventRepository

from ..converters import event_to_domain
from ..models import EventModel


class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_batch(self, events: list[Event]) -> int:
        models = []
        for ev in events:
            kwargs = {
                "id": ev.id or str(uuid.uuid4()),
                "club_id": ev.club_id,
                "match_id": ev.match_id,
                "player_id": ev.player_id,
                "player_name": ev.player_name,
                "quarter": ev.quarter,
                "team": ev.team,
                "event_type": ev.event_type,
                "subtype": ev.subtype,
                "value": ev.value,
                "note": ev.note,
                "video_timestamp": ev.video_timestamp,
            }
            for flag in EVENT_FLAG_FIELDS:
                kwargs[flag] = ev.get_flag_value(flag)
            models.append(EventModel(**kwargs))

        self.session.add_all(models)
        await self.session.flush()
        return len(models)

    async def get_recent(
        self, club_id: str, match_id: str, limit: int = 20
    ) -> list[Event]:
        result = await self.session.execute(
            select(EventModel)
            .where(EventModel.club_id == club_id, EventModel.match_id == match_id)
            .order_by(EventModel.timestamp.desc())
            .limit(limit)
        )
        return [event_to_domain(r) for r in result.scalars().all()]

    async def delete_by_id(self, club_id: str, event_id: str) -> None:
        result = await self.session.execute(
            select(EventModel)
            .where(EventModel.club_id == club_id, EventModel.id == event_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise ValueError(f"Event {event_id} not found")
        await self.session.delete(row)

    async def delete_last_within_window(
        self, club_id: str, match_id: str, minutes: int = 3
    ) -> bool:
        """Delete the most recent event within the time window. Returns True if deleted."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        result = await self.session.execute(
            select(EventModel)
            .where(
                EventModel.club_id == club_id,
                EventModel.match_id == match_id,
                EventModel.timestamp >= cutoff,
            )
            .order_by(EventModel.timestamp.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            await self.session.delete(row)
            return True
        return False

    async def get_all_for_match(self, club_id: str, match_id: str) -> list[Event]:
        result = await self.session.execute(
            select(EventModel)
            .where(EventModel.club_id == club_id, EventModel.match_id == match_id)
            .order_by(EventModel.timestamp.asc())
        )
        return [event_to_domain(r) for r in result.scalars().all()]

    async def get_all_for_club(self, club_id: str) -> list[Event]:
        result = await self.session.execute(
            select(EventModel)
            .where(EventModel.club_id == club_id)
            .order_by(EventModel.timestamp.asc())
        )
        return [event_to_domain(r) for r in result.scalars().all()]

    async def get_all_for_player(
        self, club_id: str, player_id: str, season_id: str | None = None
    ) -> list[Event]:
        query = (
            select(EventModel)
            .where(EventModel.club_id == club_id, EventModel.player_id == player_id)
            .order_by(EventModel.timestamp.asc())
        )
        # If season_id filter needed, join with matches table
        # For now return all; filtering by season is done at the service layer
        result = await self.session.execute(query)
        return [event_to_domain(r) for r in result.scalars().all()]

    async def get_all_for_season(self, club_id: str, season_id: str) -> list[Event]:
        from ..models import MatchModel
        result = await self.session.execute(
            select(EventModel)
            .join(MatchModel, EventModel.match_id == MatchModel.match_id)
            .where(EventModel.club_id == club_id, MatchModel.season_id == season_id)
            .order_by(EventModel.timestamp.asc())
        )
        return [event_to_domain(r) for r in result.scalars().all()]
