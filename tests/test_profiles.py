from pathlib import Path

import pytest

from flashrun_lab.profiles import ProfileError, load_profile, validate_profile


def _example_path() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles" / "8.6.8.example.json"


def test_load_example_profile() -> None:
    profile = load_profile(_example_path())
    assert profile.version == "8.6.8"
    assert profile.sign_key == "F44B0282BEA83557"
    assert len(profile.device_profiles) == 1


def test_validate_example_profile_raises_for_placeholder_hash() -> None:
    # The example profile is intentionally not runnable until real APK hash is filled.
    with pytest.raises(ProfileError):
        validate_profile(_example_path())
