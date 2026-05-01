import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    pass


class Lecture(IdMixin, TimestampMixin, Base):
    __tablename__ = "lectures"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chunks: Mapped[list["LectureChunk"]] = relationship(
        back_populates="lecture",
        cascade="all, delete-orphan",
    )


class LectureChunk(IdMixin, TimestampMixin, Base):
    __tablename__ = "lecture_chunks"
    __table_args__ = (
        UniqueConstraint("lecture_id", "chunk_index", name="uq_lecture_chunk_index"),
    )

    lecture_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    qdrant_point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )

    lecture: Mapped["Lecture"] = relationship(back_populates="chunks")
