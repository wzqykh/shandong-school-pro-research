"""Structured, redacted run telemetry."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    phase: str
    profile_version: str
    package: str
    status: str
    started_at: str
    finished_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunRecord":
        return cls(
            run_id=str(data["run_id"]),
            phase=str(data["phase"]),
            profile_version=str(data["profile_version"]),
            package=str(data["package"]),
            status=str(data["status"]),
            started_at=str(data["started_at"]),
            finished_at=data.get("finished_at"),
            metadata=dict(data.get("metadata", {})),
        )


def redact_secrets(text: str, secrets: list[str]) -> str:
    """Replace known secrets in a string; never return them unchanged."""
    output = text
    for secret in secrets:
        if secret:
            output = output.replace(secret, "***")
    return output


class TelemetryStore:
    """Persist run records and events as owner-only JSON/JSONL files."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.runs_dir = self.root / "runs"

    def start_run(
        self,
        phase: str,
        profile_version: str,
        package: str,
        metadata: dict[str, Any] | None = None,
    ) -> RunRecord:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        record = RunRecord(
            run_id=uuid.uuid4().hex,
            phase=phase,
            profile_version=profile_version,
            package=package,
            status="running",
            started_at=utc_now_iso(),
            metadata=metadata or {},
        )
        self._write_record(record)
        return record

    def finish_run(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> RunRecord:
        record = self.load_run(run_id)
        merged = dict(record.metadata)
        if metadata:
            merged.update(metadata)
        updated = RunRecord(
            run_id=record.run_id,
            phase=record.phase,
            profile_version=record.profile_version,
            package=record.package,
            status=status,
            started_at=record.started_at,
            finished_at=utc_now_iso(),
            metadata=merged,
        )
        self._write_record(updated)
        return updated

    def write_event(
        self,
        run_id: str,
        level: str,
        event: str,
        payload: dict[str, Any] | None = None,
        *,
        secrets: list[str] | None = None,
    ) -> None:
        record = self.load_run(run_id)
        event_path = self.runs_dir / f"{run_id}.events.jsonl"
        line = {
            "run_id": run_id,
            "phase": record.phase,
            "level": level,
            "event": event,
            "payload": payload or {},
            "timestamp": utc_now_iso(),
        }
        raw = json.dumps(line, ensure_ascii=False, sort_keys=True)
        if secrets:
            raw = redact_secrets(raw, secrets)
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(raw + "\n")
        try:
            os.chmod(event_path, 0o600)
        except OSError:
            pass

    def load_run(self, run_id: str) -> RunRecord:
        path = self.runs_dir / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return RunRecord.from_dict(raw)

    def list_runs(self) -> list[RunRecord]:
        records: list[RunRecord] = []
        for path in sorted(self.runs_dir.glob("*.json")):
            records.append(RunRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        return records

    def _write_record(self, record: RunRecord) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{record.run_id}.json"
        path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
