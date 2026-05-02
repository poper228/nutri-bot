"""Apply nutritionist's optimal ranges on top of lab-reported statuses."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.services.analysis.schemas import LabIndicator, ParsedAnalysis

_RANGES_PATH = Path(__file__).parent / "optimal_ranges.json"


def _normalize(text: str) -> str:
    """Lowercase, strip brackets/punctuation for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"[()%/\-,.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=1)
def _load_ranges() -> list[dict]:
    return json.loads(_RANGES_PATH.read_text())


def _find_optimal(name: str) -> dict | None:
    norm = _normalize(name)
    for entry in _load_ranges():
        names_to_check = [entry["name"]] + (entry.get("aliases") or [])
        for candidate in names_to_check:
            if _normalize(candidate) in norm or norm in _normalize(candidate):
                return entry
    return None


def _evaluate_status(
    value_str: str,
    optimal_min: float | None,
    optimal_max: float | None,
) -> Literal["low", "normal", "high", "unknown"] | None:
    """Return new status if we can compute it, else None."""
    if optimal_min is None and optimal_max is None:
        return None
    try:
        value = float(value_str.replace(",", ".").split()[0])
    except (ValueError, IndexError):
        return None

    if optimal_min is not None and value < optimal_min:
        return "low"
    if optimal_max is not None and value > optimal_max:
        return "high"
    if (optimal_min is None or value >= optimal_min) and (optimal_max is None or value <= optimal_max):
        return "normal"
    return None


def apply_optimal_ranges(analysis: ParsedAnalysis) -> ParsedAnalysis:
    """Return new ParsedAnalysis with statuses overridden by nutritionist's optimal ranges."""
    updated: list[LabIndicator] = []
    for ind in analysis.indicators:
        entry = _find_optimal(ind.name)
        if entry:
            new_status = _evaluate_status(ind.value, entry["optimal_min"], entry["optimal_max"])
            if new_status is not None:
                # Build a new reference string showing optimal range
                opt_min = entry["optimal_min"]
                opt_max = entry["optimal_max"]
                if opt_min is not None and opt_max is not None:
                    opt_ref = f"{opt_min}–{opt_max} (оптимум)"
                elif opt_min is not None:
                    opt_ref = f">{opt_min} (оптимум)"
                else:
                    opt_ref = f"<{opt_max} (оптимум)"

                ind = ind.model_copy(update={"status": new_status, "reference": opt_ref})
        updated.append(ind)
    return analysis.model_copy(update={"indicators": updated})
