import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Substitution
from src.domain.ports.repositories import SubstitutionRepository

from ..converters import substitution_to_domain
from ..models import SubstitutionModel


class SQLAlchemySubstitutionRepository(SubstitutionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_match(self, club_id: str, match_id: str) -> list[Substitution]:
        result = await self.session.execute(
            select(SubstitutionModel)
            .where(
                SubstitutionModel.club_id == club_id,
                SubstitutionModel.match_id == match_id,
            )
            .order_by(SubstitutionModel.timestamp.asc())
        )
        return [substitution_to_domain(r) for r in result.scalars().all()]

    async def create(self, sub: Substitution) -> Substitution:
        model = SubstitutionModel(
            id=sub.id or str(uuid.uuid4()),
            club_id=sub.club_id,
            match_id=sub.match_id,
            player_id=sub.player_id,
            direction=sub.direction,
            quarter=sub.quarter,
        )
        self.session.add(model)
        await self.session.flush()
        return substitution_to_domain(model)

    async def create_many(self, subs: list[Substitution]) -> list[Substitution]:
        models = [
            SubstitutionModel(
                id=s.id or str(uuid.uuid4()),
                club_id=s.club_id,
                match_id=s.match_id,
                player_id=s.player_id,
                direction=s.direction,
                quarter=s.quarter,
            )
            for s in subs
        ]
        self.session.add_all(models)
        await self.session.flush()
        return [substitution_to_domain(m) for m in models]
