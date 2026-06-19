import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import AgeCategory, DEFAULT_AGE_CATEGORIES
from src.domain.ports.repositories import AgeCategoryRepository

from ..converters import age_category_to_domain
from ..models import AgeCategoryModel


class SQLAlchemyAgeCategoryRepository(AgeCategoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_club(self, club_id: str) -> list[AgeCategory]:
        result = await self.session.execute(
            select(AgeCategoryModel)
            .where(AgeCategoryModel.club_id == club_id)
            .order_by(AgeCategoryModel.sort_order.asc(), AgeCategoryModel.name.asc())
        )
        return [age_category_to_domain(r) for r in result.scalars().all()]

    async def create(self, category: AgeCategory) -> AgeCategory:
        model = AgeCategoryModel(
            id=category.id or str(uuid.uuid4()),
            club_id=category.club_id,
            name=category.name,
            sort_order=category.sort_order,
        )
        self.session.add(model)
        await self.session.flush()
        return age_category_to_domain(model)

    async def update(self, category: AgeCategory) -> AgeCategory | None:
        await self.session.execute(
            update(AgeCategoryModel)
            .where(
                AgeCategoryModel.club_id == category.club_id,
                AgeCategoryModel.id == category.id,
            )
            .values(name=category.name, sort_order=category.sort_order)
        )
        await self.session.flush()
        result = await self.session.execute(
            select(AgeCategoryModel).where(AgeCategoryModel.id == category.id)
        )
        row = result.scalar_one_or_none()
        return age_category_to_domain(row) if row else None

    async def delete(self, club_id: str, category_id: str) -> None:
        await self.session.execute(
            delete(AgeCategoryModel)
            .where(
                AgeCategoryModel.club_id == club_id,
                AgeCategoryModel.id == category_id,
            )
        )

    async def seed_defaults(self, club_id: str) -> list[AgeCategory]:
        models = [
            AgeCategoryModel(
                id=str(uuid.uuid4()),
                club_id=club_id,
                name=name,
                sort_order=i,
            )
            for i, name in enumerate(DEFAULT_AGE_CATEGORIES)
        ]
        self.session.add_all(models)
        await self.session.flush()
        return [age_category_to_domain(m) for m in models]
