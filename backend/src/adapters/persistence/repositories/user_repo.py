import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import ClubMembership, User
from src.domain.ports.repositories import UserRepository

from ..converters import membership_to_domain, user_to_domain
from ..models import ClubMembershipModel, UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        row = result.scalar_one_or_none()
        return user_to_domain(row) if row else None

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        row = result.scalar_one_or_none()
        return user_to_domain(row) if row else None

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id or str(uuid.uuid4()),
            email=user.email,
            hashed_password=user.hashed_password,
        )
        self.session.add(model)
        await self.session.flush()
        return user_to_domain(model)

    async def get_memberships(self, user_id: str) -> list[ClubMembership]:
        result = await self.session.execute(
            select(ClubMembershipModel)
            .where(ClubMembershipModel.user_id == user_id)
        )
        return [membership_to_domain(r) for r in result.scalars().all()]

    async def get_membership(
        self, user_id: str, club_id: str
    ) -> ClubMembership | None:
        result = await self.session.execute(
            select(ClubMembershipModel)
            .where(
                ClubMembershipModel.user_id == user_id,
                ClubMembershipModel.club_id == club_id,
            )
        )
        row = result.scalar_one_or_none()
        return membership_to_domain(row) if row else None

    async def create_membership(self, membership: ClubMembership) -> ClubMembership:
        model = ClubMembershipModel(
            id=membership.id or str(uuid.uuid4()),
            user_id=membership.user_id,
            club_id=membership.club_id,
            role=membership.role.value,
        )
        self.session.add(model)
        await self.session.flush()
        return membership_to_domain(model)
