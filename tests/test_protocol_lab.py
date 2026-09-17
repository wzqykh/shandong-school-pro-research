import base64

import pytest

from flashrun_lab.protocol_lab import (
    EndpointSchema,
    ProtocolError,
    SignOracle,
    compute_sign,
    load_endpoint_map,
    sha256_reorder,
)


def test_sha256_reorder_swaps_first_and_last_eight() -> None:
    digest = "0" * 24 + "a" * 8 + "b" * 24 + "c" * 8
    assert len(digest) == 64
    result = sha256_reorder(digest)
    assert result == "c" * 8 + "0" * 16 + "a" * 8 + "b" * 24 + "0" * 8


def test_compute_sign_returns_base64_and_is_stable() -> None:
    payload = '{"test":123}'
    first = compute_sign(payload, "F44B0282BEA83557", "01234ABCDEF56789")
    second = compute_sign(payload, "F44B0282BEA83557", "01234ABCDEF56789")
    assert first == second
    assert base64.b64encode(base64.b64decode(first)).decode("ascii") == first


def test_oracle_rejects_wrong_signature() -> None:
    oracle = SignOracle("F44B0282BEA83557", "01234ABCDEF56789")
    sign = oracle.recompute('{"a":1}')
    assert oracle.verify_replay('{"a":1}', sign)
    assert not oracle.verify_replay('{"a":1}', "wrong")


def test_endpoint_schema_validation(tmp_path) -> None:
    data = {
        "login": {
            "name": "login",
            "method": "post",
            "path": "/api/login",
            "auth_headers": ["satoken"],
            "body_fields": ["phone", "password"],
        }
    }
    path = tmp_path / "endpoints.json"
    path.write_text(
        '{"login":{"name":"login","method":"post","path":"/api/login","auth_headers":["satoken"],"body_fields":["phone","password"]}}',
        encoding="utf-8",
    )
    loaded = load_endpoint_map(path)
    assert loaded["login"] == EndpointSchema.from_dict(data["login"])


def test_reorder_rejects_bad_length() -> None:
    with pytest.raises(ProtocolError):
        sha256_reorder("abc")
