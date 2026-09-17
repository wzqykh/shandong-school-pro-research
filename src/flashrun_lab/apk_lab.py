"""APK acquisition and static inspection utilities."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class AdbError(RuntimeError):
    """Raised when an adb command fails."""


@dataclass
class ApkInfo:
    package: str
    local_path: Path
    sha256: str
    size_bytes: int
    version_name: str | None = None
    version_code: str | None = None


class AdbRunner:
    """Thin wrapper around an ADB executable."""

    def __init__(self, adb_path: str | Path = "adb", serial: str | None = None) -> None:
        self.adb_path = str(adb_path)
        self.serial = serial

    def _base_command(self) -> list[str]:
        command = [self.adb_path]
        if self.serial:
            command.extend(["-s", self.serial])
        return command

    def run(self, *args: str, check: bool = True, timeout: int = 60) -> str:
        command = [*self._base_command(), *args]
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if check and proc.returncode != 0:
            raise AdbError(
                f"adb command failed ({proc.returncode}): {' '.join(command)}\n"
                f"stderr: {proc.stderr.strip()}"
            )
        return proc.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pull_apk(
    package: str,
    output_dir: str | Path,
    adb: AdbRunner | None = None,
) -> ApkInfo:
    """Pull the base APK for a package and return its hash."""
    runner = adb or AdbRunner()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    paths = runner.run("shell", "pm", "path", package)
    base_path = next(
        (line.split(":", 1)[1].strip() for line in paths.splitlines() if line.startswith("package:")),
        None,
    )
    if not base_path:
        raise AdbError(f"no APK path found for package {package}")

    local_path = destination / f"{package}.base.apk"
    runner.run("pull", base_path, str(local_path))
    info = ApkInfo(
        package=package,
        local_path=local_path,
        sha256=_sha256(local_path),
        size_bytes=local_path.stat().st_size,
    )
    return info


def fill_version_info(package: str, adb: AdbRunner) -> dict[str, str]:
    raw = adb.run("shell", "dumpsys", "package", package)
    version_name = None
    version_code = None
    for line in raw.splitlines():
        if "versionName=" in line and version_name is None:
            version_name = line.split("versionName=", 1)[1].split()[0]
        if "versionCode=" in line and version_code is None:
            version_code = line.split("versionCode=", 1)[1].split()[0]
    return {"versionName": version_name or "", "versionCode": version_code or ""}


def write_manifest_report(
    package: str,
    output_path: str | Path,
    adb: AdbRunner | None = None,
) -> None:
    """Write a minimal package dump report for later static analysis."""
    runner = adb or AdbRunner()
    raw = runner.run("shell", "dumpsys", "package", package)
    Path(output_path).write_text(raw, encoding="utf-8")


def locate_tool(name: str) -> str | None:
    return shutil.which(name)
