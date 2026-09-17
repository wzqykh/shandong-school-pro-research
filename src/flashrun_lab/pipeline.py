"""Small end-to-end orchestration helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .apk_lab import AdbRunner, ApkInfo, fill_version_info, pull_apk, write_manifest_report
from .profiles import AppProfile, load_profile
from .telemetry import TelemetryStore


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    report_path: Path
    apk: ApkInfo
    version: dict[str, str]


class PipelineError(RuntimeError):
    """Raised when an orchestrated phase fails."""


def run_apk_lab_pipeline(
    profile_path: str | Path,
    output_dir: str | Path,
    telemetry_dir: str | Path,
    *,
    package: str | None = None,
    adb_path: str = "adb",
    serial: str | None = None,
) -> PipelineResult:
    """Run the apk_lab phase with telemetry."""
    profile = load_profile(profile_path)
    package = package or "com.huachenjie.shandong_school_pro"
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    telemetry = TelemetryStore(telemetry_dir)
    run = telemetry.start_run(
        phase="apk_lab",
        profile_version=profile.version,
        package=package,
        metadata={"profile": str(profile_path)},
    )
    try:
        adb = AdbRunner(adb_path=adb_path, serial=serial)
        info = pull_apk(package, output, adb=adb)
        version = fill_version_info(package, adb)
        manifest_path = output / f"{package}.package_dump.txt"
        write_manifest_report(package, manifest_path, adb=adb)
        report_path = output / f"{package}.apk_report.json"
        report = {
            "package": package,
            "profile_version": profile.version,
            "sha256": info.sha256,
            "size_bytes": info.size_bytes,
            "local_path": str(info.local_path),
            "version": version,
            "manifest_dump": str(manifest_path),
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        telemetry.finish_run(run.run_id, "ok", {"report": str(report_path), "version": version})
        return PipelineResult(run_id=run.run_id, report_path=report_path, apk=info, version=version)
    except Exception as exc:
        telemetry.finish_run(run.run_id, "error", {"error": str(exc)})
        raise PipelineError(str(exc)) from exc
