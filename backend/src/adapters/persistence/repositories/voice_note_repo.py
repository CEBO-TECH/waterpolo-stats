import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import VoiceNote
from src.domain.ports.repositories import VoiceNoteRepository

from ..converters import voice_note_to_domain
from ..models import VoiceNoteModel


class SQLAlchemyVoiceNoteRepository(VoiceNoteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, note: VoiceNote) -> VoiceNote:
        model = VoiceNoteModel(
            id=note.id or str(uuid.uuid4()),
            club_id=note.club_id,
            match_id=note.match_id,
            player_id=note.player_id,
            audio_key=note.audio_key,
            content_type=note.content_type,
            duration_s=note.duration_s,
            note=note.note,
            created_by=note.created_by,
        )
        self.session.add(model)
        await self.session.flush()
        return voice_note_to_domain(model)

    async def list_for_match(self, club_id: str, match_id: str) -> list[VoiceNote]:
        result = await self.session.execute(
            select(VoiceNoteModel)
            .where(VoiceNoteModel.club_id == club_id, VoiceNoteModel.match_id == match_id)
            .order_by(VoiceNoteModel.created_at.desc())
        )
        return [voice_note_to_domain(r) for r in result.scalars().all()]

    async def get_by_id(self, club_id: str, note_id: str) -> VoiceNote | None:
        result = await self.session.execute(
            select(VoiceNoteModel)
            .where(VoiceNoteModel.club_id == club_id, VoiceNoteModel.id == note_id)
        )
        row = result.scalar_one_or_none()
        return voice_note_to_domain(row) if row else None

    async def delete(self, club_id: str, note_id: str) -> None:
        await self.session.execute(
            delete(VoiceNoteModel)
            .where(VoiceNoteModel.club_id == club_id, VoiceNoteModel.id == note_id)
        )
