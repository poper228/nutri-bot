from typing import Literal

from pydantic import BaseModel, Field


class LabIndicator(BaseModel):
    name: str = Field(description="Название показателя")
    value: str = Field(description="Значение как строка")
    unit: str | None = Field(default=None, description="Единица измерения")
    reference: str | None = Field(default=None, description="Референсный диапазон")
    status: Literal["low", "normal", "high", "unknown"] = Field(default="unknown")


class ParsedAnalysis(BaseModel):
    source_type: Literal["blood", "urine", "other", "unknown"] = Field(default="unknown")
    indicators: list[LabIndicator] = Field(default_factory=list)
