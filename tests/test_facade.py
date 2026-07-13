from anonymai import PIIType, find_pii, scrub, unscrub


def test_detect_scrub_unscrub_roundtrip():
    text = (
        "My name is Daniel and I'm from Jerusalem, I like to eat pizza. "
        "Daniel was my father's name as well."
    )

    entities = find_pii(text)
    found_types = {e.pii_type for e in entities}
    assert PIIType.PERSON in found_types
    assert PIIType.LOCATION in found_types

    result = scrub(text, exclude_pii=[PIIType.LOCATION])

    person_mentions = [e.text for e in entities if e.pii_type == PIIType.PERSON]
    assert person_mentions  # sanity check the detector actually found the name
    for mention in person_mentions:
        assert mention not in result.scrubbed_text
    assert "Jerusalem" in result.scrubbed_text  # excluded, left untouched

    assert unscrub(result.scrubbed_text, result) == text


def test_person_alias_gets_consistent_replacement():
    text = (
        "My name is Daniel Cohen and I'm from Jerusalem, I like to eat pizza. "
        "Daniel was my father's name as well."
    )

    result = scrub(text, exclude_pii=[PIIType.LOCATION])

    original_by_replacement = result.mapping
    full_name_replacement = next(r for r, o in original_by_replacement.items() if o == "Daniel Cohen")
    short_name_replacement = next(r for r, o in original_by_replacement.items() if o == "Daniel")

    assert full_name_replacement.split(" ")[0] == short_name_replacement
    assert "Daniel" not in result.scrubbed_text
    assert unscrub(result.scrubbed_text, result) == text
