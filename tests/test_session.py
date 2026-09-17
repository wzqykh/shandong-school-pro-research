import os

from flashrun_lab.session import AccountContext, SessionStore


def test_session_store_round_trip(tmp_path) -> None:
    path = tmp_path / "state" / "session.json"
    store = SessionStore(path)
    store.update_account(AccountContext(label="research-device", role="test"))

    assert path.exists()
    assert store.load()["account"]["label"] == "research-device"
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600


def test_session_store_clear(tmp_path) -> None:
    store = SessionStore(tmp_path / "session.json")
    store.update_account(AccountContext(label="x"))
    store.clear()
    assert store.load() == {}
