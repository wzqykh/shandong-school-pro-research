import pytest

from flashrun_lab.transport import (
    MockTransport,
    RequestContext,
    ResponseContext,
    TransportError,
    _parse_curl_headers,
)


def test_mock_transport_matches_method_and_url() -> None:
    expected = ResponseContext(status=200, headers={"X-Test": "1"}, body=b"ok")
    transport = MockTransport({("GET", "https://example.invalid/api"): expected})
    request = RequestContext(method="GET", url="https://example.invalid/api")

    assert transport.send(request) == expected
    assert transport.requests == [request]


def test_mock_transport_missing_response_raises() -> None:
    transport = MockTransport()
    request = RequestContext(method="POST", url="https://example.invalid/x")
    with pytest.raises(TransportError):
        transport.send(request)


def test_parse_curl_headers() -> None:
    raw = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nX-Trace: abc\r\n\r\n"
    status, headers = _parse_curl_headers(raw)
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert headers["X-Trace"] == "abc"
