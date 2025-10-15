# tests/test_basic.py
import pytest
from ui.components import helpers

def test_lookup():
    res = helpers.lookup_entity("TCS")
    assert isinstance(res, dict)

def test_hash():
    h = helpers.hash_payload({"a":1})
    assert len(h) == 64
