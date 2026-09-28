"""Specification for M5 tokens.py. Remove `pytestmark` once implemented."""

import pytest

from app.modules.groups import tokens

pytestmark = pytest.mark.todo


def test_room_code_format():
    codes = {tokens.new_room_code() for _ in range(200)}
    assert len(codes) > 190
    assert all(len(c) == 6 and set(c) <= set(tokens.ROOM_CODE_ALPHABET) for c in codes)


def test_token_hash_is_stable_and_not_plain():
    t = tokens.new_participant_token()
    assert len(t) >= 40
    assert tokens.hash_token(t) == tokens.hash_token(t) != t
    assert len(tokens.hash_token(t)) == 64
