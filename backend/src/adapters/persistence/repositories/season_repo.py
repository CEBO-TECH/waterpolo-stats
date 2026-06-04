import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Season
from src.domain.ports.repositories import SeasonRepository

from ..converters import season_to_domain
from ..models import SeasonModel


class SQLAlchemySeasonRepository(SeasonRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, season: Season) -> Season:
        model = SeasonModel(
            id=season.id or str(uuid.uuid4()),
            club_id=season.club_id,
            name=season.name,
            start_date=str(season.start_date),
            end_date=str(season.end_date),
            is_active=season.is_active,
        )
        self.session.add(model)
        await self.session.flush()
        return season_to_domain(model)

    async def list_by_club(self, club_id: str) -> list[Season]:
        result = await self.session.execute(
            select(SeasonModel)
            .where(SeasonModel.club_id == club_id)
            .order_by(SeasonModel.start_date.desc())
        )
        return [season_to_domain(r) for r in result.scalars().all()]

    async def get_active(self, club_id: str) -> Season | None:
        result = await self.session.execute(
            select(SeasonModel)
            .where(SeasonModel.club_id == club_id, SeasonModel.is_active == True)
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return season_to_domain(row) if row else None

    async def get_by_id(self, club_id: str, season_id: str) -> Season | None:
        result = await self.session.execute(
            select(SeasonModel)
            .where(SeasonModel.club_id == club_id, SeasonModel.id == season_id)
        )
        row = result.scalar_one_or_none()
        return season_to_domain(row) if row else None

    async def update(self, season: Season) -> Season:
        await self.session.execute(
            update(SeasonModel)
            .where(SeasonModel.id == season.id)
            .values(
                name=season.name,
                start_date=str(season.start_date),
                end_date=str(season.end_date),
                is_active=season.is_active,
            )
        )
        return season

    async def delete(self, club_id: str, season_id: str) -> None:
        await self.session.execute(
            delete(SeasonModel)
            .where(SeasonModel.club_id == club_id, SeasonModel.id == season_id)
        )
