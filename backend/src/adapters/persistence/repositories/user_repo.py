import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import ClubMembership, User, UserRole
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

    async def list_members(self, club_id: str) -> list[tuple[ClubMembership, str]]:
        result = await self.session.execute(
            select(ClubMembershipModel, UserModel.email)
            .join(UserModel, UserModel.id == ClubMembershipModel.user_id)
            .where(ClubMembershipModel.club_id == club_id)
            .order_by(ClubMembershipModel.created_at.asc())
        )
        return [(membership_to_domain(mm), email) for mm, email in result.all()]

    async def update_membership_role(
        self, user_id: str, club_id: str, role: UserRole
    ) -> ClubMembership | None:
        await self.session.execute(
            update(ClubMembershipModel)
            .where(
                ClubMembershipModel.user_id == user_id,
                ClubMembershipModel.club_id == club_id,
            )
            .values(role=role.value)
        )
        await self.session.flush()
        return await self.get_membership(user_id, club_id)

    async def delete_membership(self, user_id: str, club_id: str) -> None:
        await self.session.execute(
            delete(ClubMembershipModel)
            .where(
                ClubMembershipModel.user_id == user_id,
                ClubMembershipModel.club_id == club_id,
            )
        )

    async def count_owners(self, club_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ClubMembershipModel)
            .where(
                ClubMembershipModel.club_id == club_id,
                ClubMembershipModel.role == UserRole.OWNER.value,
            )
        )
        return result.scalar_one()
