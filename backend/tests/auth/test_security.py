"""Specification for M1 security.py. Remove the `pytestmark` line once implemented."""

import uuid

import pytest

from app.modules.auth import security

pytestmark = pytest.mark.todo


def test_hash_is_not_plaintext_and_verifies():
    h = security.hash_password("matkhau123")
    assert h != "matkhau123" and h.startswith("$2")
    assert security.verify_password("matkhau123", h)
    assert not security.verify_password("sai-mat-khau", h)


def test_same_password_different_hash():  # random salt
    assert security.hash_password("abcdefgh") != security.hash_password("abcdefgh")


def test_token_roundtrip():
    uid = uuid.uuid4()
    assert security.decode_access_token(security.create_access_token(uid, "ha")) == (uid, "ha")


def test_tampered_token_rejected():
    token = security.create_access_token(uuid.uuid4(), "ha")
    assert security.decode_access_token(token[:-2] + ("A" if token[-1] != "A" else "B") * 2) is None


def test_bad_token_returns_none():
    assert security.decode_access_token("khong.phai.jwt") is None
