from app.services.tshark import parse_tshark_output


def test_tshark_parser_empty_input() -> None:
    assert parse_tshark_output("") == []


def test_tshark_parser_detects_credential_in_json() -> None:
    payload = '[{"layers": {"http": {"http.file_data": "api_key=abc123"}}}]'
    findings = parse_tshark_output(payload)
    assert len(findings) == 1
    assert findings[0]["severity"] == "HIGH"
    assert findings[0]["source"] == "tshark"


def test_tshark_parser_detects_authorization_header_in_text() -> None:
    payload = 'frame: Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='
    findings = parse_tshark_output(payload)
    assert len(findings) == 1
    assert findings[0]["severity"] == "HIGH"


def test_tshark_parser_ignores_benign_payload() -> None:
    payload = '[{"layers": {"frame": {"frame.length": "120"}}}]'
    assert parse_tshark_output(payload) == []
