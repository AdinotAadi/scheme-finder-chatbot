"""
tests/test_profile_extractor.py - Tests for conversational demographic attribute extraction and triage.
"""

import pytest
from src.schema.rules import UserProfile
from src.engine.profile_extractor import extract_attributes_from_messages, get_missing_essential_attributes

def test_missing_attributes_on_empty_profile():
    empty_p = UserProfile()
    missing = get_missing_essential_attributes(empty_p)
    assert "state_residence" in missing
    assert "gender" in missing
    assert "age" in missing

def test_incremental_extraction():
    # Turn 1: User gives vague query
    messages = [{"role": "user", "content": "I want to look for health schemes for myself."}]
    p1 = extract_attributes_from_messages(messages)
    missing1 = get_missing_essential_attributes(p1)
    assert len(missing1) == 3

    # Turn 2: User provides state and age
    messages.append({"role": "assistant", "content": "Could you provide your state, age, and gender?"})
    messages.append({"role": "user", "content": "I live in Uttarakhand and I am 16 years old."})
    p2 = extract_attributes_from_messages(messages, p1)
    assert p2.state_residence == "Uttarakhand"
    assert p2.age == 16
    assert p2.gender is None
    missing2 = get_missing_essential_attributes(p2)
    assert missing2 == ["gender"]

    # Turn 3: User clarifies gender
    messages.append({"role": "user", "content": "I am a girl."})
    p3 = extract_attributes_from_messages(messages, p2)
    assert p3.gender == "female"
    assert len(get_missing_essential_attributes(p3)) == 0

