from fastapi.testclient import TestClient

from anonymai.api import app

client = TestClient(app)


def test_pii_scrub_unscrub_roundtrip():
    text = (
        "My name is Daniel and I'm from Jerusalem, I like to eat pizza. "
        "Daniel was my father's name as well."
    )

    pii_response = client.post("/pii", json={"text": text})
    assert pii_response.status_code == 200
    found_types = {e["pii_type"] for e in pii_response.json()}
    assert "PERSON" in found_types
    assert "LOCATION" in found_types

    scrub_response = client.post(
        "/scrub", json={"text": text, "exclude_pii": ["LOCATION"]}
    )
    assert scrub_response.status_code == 200
    result = scrub_response.json()
    assert "Daniel" not in result["scrubbed_text"]
    assert "Jerusalem" in result["scrubbed_text"]  # excluded, left untouched

    unscrub_response = client.post(
        "/unscrub", json={"text": result["scrubbed_text"], "mapping": result["mapping"]}
    )
    assert unscrub_response.status_code == 200
    assert unscrub_response.json()["text"] == text
