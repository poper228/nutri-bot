from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import AnalysisSourceType, AnalysisStatus

if TYPE_CHECKING:
    from app.models.user import User


class Analysis(IdMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[AnalysisSourceType] = mapped_column(
        SAEnum(AnalysisSourceType, name="analysis_source_type"),
        nullable=False,
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="analysis_status"),
        default=AnalysisStatus.pending,
        nullable=False,
        index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="analyses")
    indicators: Mapped[list["AnalysisIndicator"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class AnalysisIndicator(IdMixin, TimestampMixin, Base):
    __tablename__ = "analysis_indicators"

    analysis_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    is_deviation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    analysis: Mapped["Analysis"] = relationship(back_populates="indicators")
