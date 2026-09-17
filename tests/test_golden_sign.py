from flashrun_lab.protocol_lab import compute_sign


def test_golden_sign_8_6_8() -> None:
    payload = '{"seq":1,"deviceId":"test-device-001"}'
    expected = (
        "YVIKakSKMkN34OYqBVC8PsnGSM7ufgPSkJj6Zd3KYl3zbYUXn/JImp+Sva9fgDWi//HcPQKIRS4xFJviAP3L2FSgBSfTY4DsEyTUmR6HT58="
    )
    actual = compute_sign(payload, "F44B0282BEA83557", "01234ABCDEF56789")
    assert actual == expected
