import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import ClubInvitation
from src.domain.ports.repositories import ClubInvitationRepository

from ..converters import invitation_to_domain
from ..models import ClubInvitationModel


class SQLAlchemyClubInvitationRepository(ClubInvitationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, invitation: ClubInvitation) -> ClubInvitation:
        model = ClubInvitationModel(
            id=invitation.id or str(uuid.uuid4()),
            club_id=invitation.club_id,
            email=invitation.email,
            role=invitation.role.value,
            token=invitation.token,
            status=invitation.status,
        )
        self.session.add(model)
        await self.session.flush()
        return invitation_to_domain(model)

    async def list_pending(self, club_id: str) -> list[ClubInvitation]:
        result = await self.session.execute(
            select(ClubInvitationModel)
            .where(
                ClubInvitationModel.club_id == club_id,
                ClubInvitationModel.status == "pending",
            )
            .order_by(ClubInvitationModel.created_at.asc())
        )
        return [invitation_to_domain(r) for r in result.scalars().all()]

    async def get_by_token(self, token: str) -> ClubInvitation | None:
        result = await self.session.execute(
            select(ClubInvitationModel).where(ClubInvitationModel.token == token)
        )
        row = result.scalar_one_or_none()
        return invitation_to_domain(row) if row else None

    async def update_status(self, invitation_id: str, status: str) -> None:
        await self.session.execute(
            update(ClubInvitationModel)
            .where(ClubInvitationModel.id == invitation_id)
            .values(status=status)
        )

    async def delete(self, club_id: str, invitation_id: str) -> None:
        await self.session.execute(
            delete(ClubInvitationModel)
            .where(
                ClubInvitationModel.club_id == club_id,
                ClubInvitationModel.id == invitation_id,
            )
        )
