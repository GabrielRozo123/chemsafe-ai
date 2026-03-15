from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PropertyValue:
    value: Any
    unit: str = ""
    source: str = ""
    confidence: str = "seed"


@dataclass
class CompoundProfile:
    identity: Dict[str, Any] = field(default_factory=dict)
    hazards: List[str] = field(default_factory=list)
    nfpa: Dict[str, Any] = field(default_factory=dict)

    physchem: Dict[str, PropertyValue] = field(default_factory=dict)
    exposure_limits: Dict[str, PropertyValue] = field(default_factory=dict)
    reactivity: Dict[str, Any] = field(default_factory=dict)
    storage: Dict[str, Any] = field(default_factory=dict)

    flags: Dict[str, bool] = field(default_factory=dict)
    fingerprint: Dict[str, float] = field(default_factory=dict)
    routing: List[str] = field(default_factory=list)
    validation_gaps: List[str] = field(default_factory=list)

    source_trace: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)

    def prop(self, key: str, default: Optional[Any] = None) -> Any:
        item = self.physchem.get(key)
        if item is None:
            return default
        return item.value

    def limit(self, key: str, default: Optional[Any] = None) -> Any:
        item = self.exposure_limits.get(key)
        if item is None:
            return default
        return item.value

    def to_flat_physchem(self) -> List[Dict[str, Any]]:
        rows = []
        for key, item in self.physchem.items():
            rows.append(
                {
                    "property": key,
                    "value": item.value,
                    "unit": item.unit,
                    "source": item.source,
                    "confidence": item.confidence,
                }
            )
        return rows

    def to_flat_limits(self) -> List[Dict[str, Any]]:
        rows = []
        for key, item in self.exposure_limits.items():
            rows.append(
                {
                    "limit": key,
                    "value": item.value,
                    "unit": item.unit,
                    "source": item.source,
                    "confidence": item.confidence,
                }
            )
        return rows
