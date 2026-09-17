"""Version and device profile management."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


class ProfileError(ValueError):
    """Raised when a profile is invalid."""


@dataclass(frozen=True)
class DeviceProfile:
    device_id: str
    model: str
    system_version: str
    platform: str
    ua: str
    network_context: str = "mobile"
    binding_status: str = "unknown"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceProfile":
        required = ("device_id", "model", "system_version", "platform", "ua")
        missing = [key for key in required if key not in data]
        if missing:
            raise ProfileError(f"device profile missing fields: {missing}")
        return cls(
            device_id=str(data["device_id"]),
            model=str(data["model"]),
            system_version=str(data["system_version"]),
            platform=str(data["platform"]),
            ua=str(data["ua"]),
            network_context=str(data.get("network_context", "mobile")),
            binding_status=str(data.get("binding_status", "unknown")),
        )


@dataclass(frozen=True)
class AppProfile:
    version: str
    app_version: str
    build_version: str
    apk_sha256: str
    sign_key: str
    iv: str
    captcha_key: str
    base_url: str
    common_headers: dict[str, str]
    endpoint_map: dict[str, str]
    device_profiles: tuple[DeviceProfile, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppProfile":
        required = (
            "version",
            "app_version",
            "build_version",
            "apk_sha256",
            "sign_key",
            "iv",
            "captcha_key",
            "base_url",
            "common_headers",
            "endpoint_map",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise ProfileError(f"profile missing fields: {missing}")

        devices = tuple(
            DeviceProfile.from_dict(item) for item in data.get("device_profiles", [])
        )
        return cls(
            version=str(data["version"]),
            app_version=str(data["app_version"]),
            build_version=str(data["build_version"]),
            apk_sha256=str(data["apk_sha256"]),
            sign_key=str(data["sign_key"]),
            iv=str(data["iv"]),
            captcha_key=str(data["captcha_key"]),
            base_url=str(data["base_url"]),
            common_headers=dict(data["common_headers"]),
            endpoint_map=dict(data["endpoint_map"]),
            device_profiles=devices,
        )


def load_profile(path: str | Path) -> AppProfile:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppProfile.from_dict(raw)


def validate_profile(path: str | Path) -> None:
    profile = load_profile(path)
    if profile.apk_sha256.startswith("replace_"):
        raise ProfileError("apk_sha256 is still a placeholder")
    if not profile.sign_key:
        raise ProfileError("sign_key must not be empty")
    if not profile.base_url:
        raise ProfileError("base_url must not be empty")
    if not profile.device_profiles:
        raise ProfileError("at least one device profile is required")
