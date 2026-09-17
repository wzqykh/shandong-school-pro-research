"""Detection surface mapping and severity assessment."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


class DetectionLayer(str, Enum):
    JAVA = "java"
    NATIVE = "native"
    NETWORK = "network"
    BEHAVIOR = "behavior"
    SYSTEM = "system"


class DetectionSeverity(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectionPoint:
    point_id: str
    layer: DetectionLayer
    category: str
    severity: DetectionSeverity
    evidence: str
    notes: str = ""
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["layer"] = self.layer.value
        data["severity"] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectionPoint":
        return cls(
            point_id=str(data["point_id"]),
            layer=DetectionLayer(data["layer"]),
            category=str(data["category"]),
            severity=DetectionSeverity(data["severity"]),
            evidence=str(data["evidence"]),
            notes=str(data.get("notes", "")),
            weight=float(data.get("weight", 1.0)),
        )


DEFAULT_PATTERNS: dict[str, tuple[str, ...]] = {
    "hook": ("frida", "xposed", "lsposed", "substrate", "riru", "zygisk"),
    "root": ("magisk", "su", "superuser", "rootcloak"),
    "debug": ("ptrace", "debugger", "jdwp", "TracerPid"),
    "integrity": ("tamper", "signature", "checksum", "prologue"),
    "environment": ("emulator", "qemu", "goldfish", "nox", "genymotion"),
}


def scan_text_for_patterns(
    text: str,
    patterns: dict[str, tuple[str, ...]] | None = None,
) -> list[tuple[str, str]]:
    """Return (category, matched_string) pairs for a block of text."""
    patterns = patterns or DEFAULT_PATTERNS
    lowered = text.lower()
    findings: list[tuple[str, str]] = []
    for category, needles in patterns.items():
        for needle in needles:
            if needle.lower() in lowered:
                findings.append((category, needle))
    return findings


@dataclass
class DetectionMatrix:
    points: list[DetectionPoint] = field(default_factory=list)

    def add(self, point: DetectionPoint) -> None:
        self.points.append(point)

    def filter(
        self,
        *,
        layer: DetectionLayer | None = None,
        severity: DetectionSeverity | None = None,
    ) -> list[DetectionPoint]:
        output = self.points
        if layer is not None:
            output = [point for point in output if point.layer == layer]
        if severity is not None:
            output = [point for point in output if point.severity == severity]
        return output

    def to_dict(self) -> dict[str, Any]:
        return {"points": [point.to_dict() for point in self.points]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectionMatrix":
        return cls(points=[DetectionPoint.from_dict(item) for item in data.get("points", [])])

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, path: str | Path) -> "DetectionMatrix":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    def to_markdown(self) -> str:
        if not self.points:
            return "| point_id | layer | category | severity | evidence |\n|---|---|---|---|---|"
        lines = [
            "| point_id | layer | category | severity | evidence |",
            "|---|---|---|---|---|",
        ]
        for point in self.points:
            lines.append(
                f"| {point.point_id} | {point.layer.value} | {point.category} | "
                f"{point.severity.value} | {point.evidence} |"
            )
        return "\n".join(lines)
