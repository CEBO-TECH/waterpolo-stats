import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import ClubSettings
from src.domain.ports.repositories import SettingsRepository

from ..converters import settings_to_domain
from ..models import ClubSettingsModel


class SQLAlchemySettingsRepository(SettingsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_club(self, club_id: str) -> ClubSettings:
        result = await self.session.execute(
            select(ClubSettingsModel).where(ClubSettingsModel.club_id == club_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return await self.create_default(club_id)
        return settings_to_domain(row)

    async def set_active_match(self, club_id: str, match_id: str) -> ClubSettings:
        await self.session.execute(
            update(ClubSettingsModel)
            .where(ClubSettingsModel.club_id == club_id)
            .values(active_match=match_id)
        )
        return await self.get_for_club(club_id)

    async def set_quarter(self, club_id: str, quarter: int) -> ClubSettings:
        await self.session.execute(
            update(ClubSettingsModel)
            .where(ClubSettingsModel.club_id == club_id)
            .values(quarter=quarter)
        )
        return await self.get_for_club(club_id)

    async def create_default(self, club_id: str) -> ClubSettings:
        model = ClubSettingsModel(
            id=str(uuid.uuid4()),
            club_id=club_id,
            active_match="",
            quarter=1,
            editor_pin="",
        )
        self.session.add(model)
        await self.session.flush()
        return settings_to_domain(model)
