import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecture, LectureChunk


@dataclass(frozen=True, slots=True)
class ChunkInput:
    chunk_index: int
    page_number: int
    text: str
    qdrant_point_id: uuid.UUID


class LectureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_file_path(self, file_path: str) -> Lecture | None:
        result = await self._session.execute(
            select(Lecture).where(Lecture.file_path == file_path)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, lecture_id: int) -> Lecture | None:
        return await self._session.get(Lecture, lecture_id)

    async def create(
        self,
        *,
        filename: str,
        file_path: str,
        title: str | None = None,
    ) -> Lecture:
        lecture = Lecture(filename=filename, file_path=file_path, title=title)
        self._session.add(lecture)
        await self._session.flush()
        return lecture

    async def add_chunks(
        self,
        lecture_id: int,
        chunks: Sequence[ChunkInput],
    ) -> list[LectureChunk]:
        records = [
            LectureChunk(
                lecture_id=lecture_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text=c.text,
                qdrant_point_id=c.qdrant_point_id,
            )
            for c in chunks
        ]
        self._session.add_all(records)
        await self._session.flush()
        return records

    async def mark_indexed(self, lecture_id: int, indexed_at: datetime) -> None:
        await self._session.execute(
            update(Lecture).where(Lecture.id == lecture_id).values(indexed_at=indexed_at)
        )

    async def get_chunks_by_point_ids(
        self,
        point_ids: Sequence[uuid.UUID],
    ) -> list[LectureChunk]:
        if not point_ids:
            return []
        result = await self._session.execute(
            select(LectureChunk).where(LectureChunk.qdrant_point_id.in_(point_ids))
        )
        return list(result.scalars().all())
