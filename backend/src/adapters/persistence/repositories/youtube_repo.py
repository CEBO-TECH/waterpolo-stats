import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import YouTubeStream
from src.domain.ports.repositories import YouTubeStreamRepository

from ..converters import youtube_to_domain
from ..models import YouTubeStreamModel


class SQLAlchemyYouTubeStreamRepository(YouTubeStreamRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_match(self, match_id: str) -> YouTubeStream | None:
        result = await self.session.execute(
            select(YouTubeStreamModel)
            .where(YouTubeStreamModel.match_id == match_id)
        )
        row = result.scalar_one_or_none()
        return youtube_to_domain(row) if row else None

    async def create(self, stream: YouTubeStream) -> YouTubeStream:
        model = YouTubeStreamModel(
            id=stream.id or str(uuid.uuid4()),
            match_id=stream.match_id,
            youtube_url=stream.youtube_url,
            video_id=stream.video_id,
            stream_start_time=stream.stream_start_time,
        )
        self.session.add(model)
        await self.session.flush()
        return youtube_to_domain(model)

    async def update(self, stream: YouTubeStream) -> YouTubeStream:
        await self.session.execute(
            update(YouTubeStreamModel)
            .where(YouTubeStreamModel.match_id == stream.match_id)
            .values(
                youtube_url=stream.youtube_url,
                video_id=stream.video_id,
                stream_start_time=stream.stream_start_time,
            )
        )
        return stream

    async def delete(self, match_id: str) -> None:
        await self.session.execute(
            delete(YouTubeStreamModel)
            .where(YouTubeStreamModel.match_id == match_id)
        )
