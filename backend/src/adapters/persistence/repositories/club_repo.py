import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Club
from src.domain.ports.repositories import ClubRepository

from ..converters import club_to_domain
from ..models import ClubModel


class SQLAlchemyClubRepository(ClubRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, club: Club) -> Club:
        model = ClubModel(
            id=club.id or str(uuid.uuid4()),
            name=club.name,
            club_type=club.club_type.value,
        )
        self.session.add(model)
        await self.session.flush()
        return club_to_domain(model)

    async def get_by_id(self, club_id: str) -> Club | None:
        result = await self.session.execute(
            select(ClubModel).where(ClubModel.id == club_id)
        )
        row = result.scalar_one_or_none()
        return club_to_domain(row) if row else None

    async def list_all(self) -> list[Club]:
        result = await self.session.execute(
            select(ClubModel).order_by(ClubModel.name)
        )
        return [club_to_domain(r) for r in result.scalars().all()]
