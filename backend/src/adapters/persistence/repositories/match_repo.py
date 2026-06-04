import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Match, MatchStatus
from src.domain.ports.repositories import MatchRepository

from ..converters import match_to_domain
from ..models import MatchModel


class SQLAlchemyMatchRepository(MatchRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self, club_id: str) -> list[Match]:
        result = await self.session.execute(
            select(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.archived == False)
            .order_by(MatchModel.created_at.desc())
        )
        return [match_to_domain(r) for r in result.scalars().all()]

    async def list_by_season(self, club_id: str, season_id: str) -> list[Match]:
        result = await self.session.execute(
            select(MatchModel)
            .where(
                MatchModel.club_id == club_id,
                MatchModel.season_id == season_id,
                MatchModel.archived == False,
            )
            .order_by(MatchModel.created_at.desc())
        )
        return [match_to_domain(r) for r in result.scalars().all()]

    async def get_by_match_id(self, club_id: str, match_id: str) -> Match | None:
        result = await self.session.execute(
            select(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == match_id)
        )
        row = result.scalar_one_or_none()
        return match_to_domain(row) if row else None

    async def upsert(self, match: Match) -> Match:
        existing = await self.session.execute(
            select(MatchModel).where(MatchModel.match_id == match.match_id)
        )
        row = existing.scalar_one_or_none()

        if row:
            row.date = match.date
            row.opponent = match.opponent
            row.place = match.place
            row.age_category = match.age_category
            row.season_id = match.season_id
        else:
            row = MatchModel(
                id=match.id or str(uuid.uuid4()),
                club_id=match.club_id,
                match_id=match.match_id,
                date=match.date,
                opponent=match.opponent,
                place=match.place,
                age_category=match.age_category,
                season_id=match.season_id,
            )
            self.session.add(row)

        await self.session.flush()
        return match_to_domain(row)

    async def update_status(
        self, club_id: str, match_id: str, status: MatchStatus
    ) -> Match:
        await self.session.execute(
            update(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == match_id)
            .values(status=status.value)
        )
        return await self.get_by_match_id(club_id, match_id)  # type: ignore

    async def update_fields(self, club_id: str, match_id: str, fields: dict) -> Match:
        await self.session.execute(
            update(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == match_id)
            .values(**fields)
        )
        return await self.get_by_match_id(club_id, match_id)  # type: ignore

    async def archive(self, club_id: str, match_id: str) -> None:
        await self.session.execute(
            update(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == match_id)
            .values(archived=True)
        )

    async def update_scores(self, club_id: str, match_id: str, scores: dict) -> Match:
        await self.session.execute(
            update(MatchModel)
            .where(MatchModel.club_id == club_id, MatchModel.match_id == match_id)
            .values(**scores)
        )
        return await self.get_by_match_id(club_id, match_id)  # type: ignore
