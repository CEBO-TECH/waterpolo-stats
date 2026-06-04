import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import ClubConfig
from src.domain.models.config import AVAILABLE_MODULES
from src.domain.ports.repositories import ClubConfigRepository

from ..converters import config_to_domain
from ..models import ClubConfigModel


class SQLAlchemyClubConfigRepository(ClubConfigRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_club(self, club_id: str) -> ClubConfig:
        result = await self.session.execute(
            select(ClubConfigModel).where(ClubConfigModel.club_id == club_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return await self.create_default(club_id)
        return config_to_domain(row)

    async def update(self, config: ClubConfig) -> ClubConfig:
        await self.session.execute(
            update(ClubConfigModel)
            .where(ClubConfigModel.club_id == config.club_id)
            .values(
                active_modules=config.active_modules,
                button_layout=config.button_layout,
            )
        )
        return config

    async def create_default(self, club_id: str) -> ClubConfig:
        model = ClubConfigModel(
            id=str(uuid.uuid4()),
            club_id=club_id,
            active_modules=list(AVAILABLE_MODULES),
            button_layout={},
        )
        self.session.add(model)
        await self.session.flush()
        return config_to_domain(model)
