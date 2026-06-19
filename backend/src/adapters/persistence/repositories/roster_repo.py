import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import RosterEntry
from src.domain.ports.repositories import RosterRepository

from ..converters import roster_to_domain
from ..models import MatchModel, MatchRosterModel


class SQLAlchemyRosterRepository(RosterRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_match(self, club_id: str, match_id: str) -> list[RosterEntry]:
        result = await self.session.execute(
            select(MatchRosterModel)
            .where(
                MatchRosterModel.club_id == club_id,
                MatchRosterModel.match_id == match_id,
            )
            .order_by(MatchRosterModel.number.asc())
        )
        return [roster_to_domain(r) for r in result.scalars().all()]

    async def replace_for_match(
        self, club_id: str, match_id: str, entries: list[RosterEntry]
    ) -> list[RosterEntry]:
        # Delete existing roster
        await self.session.execute(
            delete(MatchRosterModel)
            .where(
                MatchRosterModel.club_id == club_id,
                MatchRosterModel.match_id == match_id,
            )
        )
        # Insert new
        models = [
            MatchRosterModel(
                id=e.id or str(uuid.uuid4()),
                club_id=club_id,
                match_id=match_id,
                player_id=e.player_id,
                number=e.number,
                name=e.name,
                team=e.team,
            )
            for e in entries
        ]
        self.session.add_all(models)
        await self.session.flush()
        return [roster_to_domain(m) for m in models]

    async def get_match_ids_for_player(self, club_id: str, player_id: str) -> list[str]:
        result = await self.session.execute(
            select(MatchRosterModel.match_id)
            .where(
                MatchRosterModel.club_id == club_id,
                MatchRosterModel.player_id == player_id,
            )
        )
        return [r for r in result.scalars().all()]

    async def get_counts_for_club(self, club_id: str) -> dict[str, int]:
        """Roster size per match for a club (one query)."""
        result = await self.session.execute(
            select(MatchRosterModel.match_id, func.count(MatchRosterModel.id))
            .where(MatchRosterModel.club_id == club_id)
            .group_by(MatchRosterModel.match_id)
        )
        return {match_id: count for match_id, count in result.all()}

    async def get_previous_match_roster(
        self, club_id: str, current_match_id: str
    ) -> list[RosterEntry]:
        """Find the previous match (by date/created_at) and return its roster.

        Port of app/api/matches/previous-roster/route.ts logic.
        """
        # Get current match to find its date
        current = await self.session.execute(
            select(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == current_match_id)
        )
        current_match = current.scalar_one_or_none()
        if not current_match:
            return []

        # Find previous match (by created_at, excluding current)
        prev_result = await self.session.execute(
            select(MatchModel)
            .where(
                MatchModel.club_id == club_id,
                MatchModel.match_id != current_match_id,
                MatchModel.archived == False,
            )
            .order_by(MatchModel.created_at.desc())
            .limit(1)
        )
        prev_match = prev_result.scalar_one_or_none()
        if not prev_match:
            return []

        return await self.get_for_match(club_id, prev_match.match_id)
