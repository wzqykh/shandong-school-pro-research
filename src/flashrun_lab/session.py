"""Account context and restricted session persistence."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SessionError(RuntimeError):
    """Raised when session state cannot be persisted or loaded."""


@dataclass(frozen=True)
class AccountContext:
    label: str
    role: str = "test"
    package: str = "com.huachenjie.shandong_school_pro"
    metadata: dict[str, Any] = field(default_factory=dict)

    def display(self) -> str:
        return f"{self.label} [{self.role}]"


class SessionStore:
    """JSON session store with owner-only file permissions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _prepare(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SessionError(f"cannot load session: {exc}") from exc
        if not isinstance(data, dict):
            raise SessionError("session root must be a JSON object")
        return data

    def save(self, data: dict[str, Any]) -> None:
        self._prepare()
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            # On filesystems without POSIX permissions, keep going but log nothing sensitive.
            pass

    def update_account(self, account: AccountContext) -> None:
        data = self.load()
        data["account"] = {
            "label": account.label,
            "role": account.role,
            "package": account.package,
            "metadata": account.metadata,
        }
        self.save(data)

    def clear(self) -> None:
        self.save({})
