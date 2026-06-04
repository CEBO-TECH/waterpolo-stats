import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Player, PlayerAgeCategory
from src.domain.ports.repositories import PlayerRepository

from ..converters import player_age_cat_to_domain, player_to_domain
from ..models import PlayerAgeCategoryModel, PlayerModel


class SQLAlchemyPlayerRepository(PlayerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_club(self, club_id: str) -> list[Player]:
        result = await self.session.execute(
            select(PlayerModel)
            .where(PlayerModel.club_id == club_id)
            .order_by(PlayerModel.number.asc())
        )
        return [player_to_domain(r) for r in result.scalars().all()]

    async def get_by_player_id(self, club_id: str, player_id: str) -> Player | None:
        result = await self.session.execute(
            select(PlayerModel)
            .where(PlayerModel.club_id == club_id, PlayerModel.player_id == player_id)
        )
        row = result.scalar_one_or_none()
        return player_to_domain(row) if row else None

    async def create(self, player: Player) -> Player:
        model = PlayerModel(
            id=player.id or str(uuid.uuid4()),
            club_id=player.club_id,
            player_id=player.player_id,
            number=player.number,
            name=player.name,
            team=player.team,
        )
        self.session.add(model)
        await self.session.flush()
        return player_to_domain(model)

    async def delete(self, club_id: str, player_id: str) -> None:
        await self.session.execute(
            delete(PlayerModel)
            .where(PlayerModel.club_id == club_id, PlayerModel.player_id == player_id)
        )

    async def exists_with_number(self, club_id: str, number: int) -> bool:
        result = await self.session.execute(
            select(PlayerModel.id)
            .where(PlayerModel.club_id == club_id, PlayerModel.number == number)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_age_categories(self, player_id: str) -> list[PlayerAgeCategory]:
        result = await self.session.execute(
            select(PlayerAgeCategoryModel)
            .where(PlayerAgeCategoryModel.player_id == player_id)
        )
        return [player_age_cat_to_domain(r) for r in result.scalars().all()]

    async def set_age_categories(
        self, player_id: str, categories: list[str]
    ) -> list[PlayerAgeCategory]:
        # Delete existing
        await self.session.execute(
            delete(PlayerAgeCategoryModel)
            .where(PlayerAgeCategoryModel.player_id == player_id)
        )
        # Insert new
        models = [
            PlayerAgeCategoryModel(
                id=str(uuid.uuid4()),
                player_id=player_id,
                age_category=cat,
            )
            for cat in categories
        ]
        self.session.add_all(models)
        await self.session.flush()
        return [player_age_cat_to_domain(m) for m in models]
