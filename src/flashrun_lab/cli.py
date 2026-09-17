"""Command line entry points for FlashRun Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .apk_lab import AdbRunner, fill_version_info, pull_apk, write_manifest_report
from .profiles import load_profile, validate_profile
from .protocol_lab import SignOracle


def _parse_profile_validate(args: argparse.Namespace) -> int:
    validate_profile(args.profile)
    print(f"profile ok: {args.profile}")
    return 0


def _parse_apk_fetch(args: argparse.Namespace) -> int:
    adb = AdbRunner(adb_path=args.adb, serial=args.serial)
    info = pull_apk(args.package, args.output_dir, adb=adb)
    version = fill_version_info(args.package, adb)
    report = {
        "package": info.package,
        "local_path": str(info.local_path),
        "sha256": info.sha256,
        "size_bytes": info.size_bytes,
        "versionName": version["versionName"],
        "versionCode": version["versionCode"],
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0


def _parse_apk_manifest(args: argparse.Namespace) -> int:
    adb = AdbRunner(adb_path=args.adb, serial=args.serial)
    write_manifest_report(args.package, args.output, adb=adb)
    print(f"manifest dump written to {args.output}")
    return 0


def _parse_sign(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    payload = Path(args.payload).read_text(encoding="utf-8")
    oracle = SignOracle(profile.sign_key, profile.iv)
    print(oracle.recompute(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flashrun")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile = subparsers.add_parser("profile", help="Profile management")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_validate = profile_sub.add_parser("validate", help="Validate a profile file")
    profile_validate.add_argument("profile")
    profile_validate.set_defaults(func=_parse_profile_validate)

    apk = subparsers.add_parser("apk", help="APK acquisition and inspection")
    apk_sub = apk.add_subparsers(dest="apk_command", required=True)

    apk_fetch = apk_sub.add_parser("fetch", help="Pull and hash an APK")
    apk_fetch.add_argument("package")
    apk_fetch.add_argument("output_dir")
    apk_fetch.add_argument("--adb", default="adb")
    apk_fetch.add_argument("--serial", default=None)
    apk_fetch.add_argument("--json", action="store_true")
    apk_fetch.set_defaults(func=_parse_apk_fetch)

    apk_manifest = apk_sub.add_parser("manifest", help="Write package dump")
    apk_manifest.add_argument("package")
    apk_manifest.add_argument("output")
    apk_manifest.add_argument("--adb", default="adb")
    apk_manifest.add_argument("--serial", default=None)
    apk_manifest.set_defaults(func=_parse_apk_manifest)

    sign = subparsers.add_parser("sign", help="Recompute a signature from a profile and payload")
    sign.add_argument("profile")
    sign.add_argument("payload")
    sign.set_defaults(func=_parse_sign)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
