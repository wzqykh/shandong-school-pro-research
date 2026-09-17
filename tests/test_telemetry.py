from flashrun_lab.telemetry import TelemetryStore, redact_secrets


def test_redact_secrets() -> None:
    assert redact_secrets("token=abc123", ["abc123"]) == "token=***"


def test_telemetry_lifecycle(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "telemetry")
    record = store.start_run(
        phase="apk_lab",
        profile_version="8.6.8",
        package="com.huachenjie.shandong_school_pro",
        metadata={"apk_sha256": "abc"},
    )
    assert record.status == "running"

    store.write_event(record.run_id, "info", "apk_pulled", {"sha256": "abc"})
    finished = store.finish_run(record.run_id, "ok", {"files": 2})
    assert finished.status == "ok"
    assert finished.finished_at
    assert store.load_run(record.run_id) == finished
    assert len(store.list_runs()) == 1


def test_write_event_redacts_secrets(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "telemetry")
    record = store.start_run("test", "1", "pkg")
    store.write_event(record.run_id, "info", "login", {"token": "secret-token"}, secrets=["secret-token"])
    event_path = store.runs_dir / f"{record.run_id}.events.jsonl"
    raw = event_path.read_text(encoding="utf-8")
    assert "secret-token" not in raw
    assert "***" in raw
