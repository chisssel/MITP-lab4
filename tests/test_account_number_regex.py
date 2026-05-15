import re
import pytest

from app.schemas import ACCOUNT_NUMBER_PATTERN

VALID = [
    "001-00001",
    "999-12345",
    "000-00000",
    "123-45678",
    "555-99999",
]

INVALID = [
    pytest.param("001-0001", id="4 digits after dash"),
    pytest.param("001-000001", id="6 digits after dash"),
    pytest.param("00100001", id="no dash"),
    pytest.param("abc-12345", id="letters before dash"),
    pytest.param("123-abcde", id="letters after dash"),
    pytest.param("01-00001", id="2 digits before dash"),
    pytest.param("0001-00001", id="4 digits before dash"),
    pytest.param("", id="empty string"),
    pytest.param(" 001-00001", id="leading space"),
    pytest.param("001-00001 ", id="trailing space"),
    pytest.param("AAA-11111", id="uppercase letters"),
    pytest.param("0-0-0-0", id="multiple dashes"),
    pytest.param("---", id="only dashes"),
    pytest.param("1-2", id="too short"),
]


class TestRegexPattern:
    def test_matches_valid(self):
        compiled = re.compile(ACCOUNT_NUMBER_PATTERN)
        for case in VALID:
            assert compiled.fullmatch(case), f"expected VALID: {case!r}"

    @pytest.mark.parametrize("value", INVALID)
    def test_rejects_invalid(self, value):
        compiled = re.compile(ACCOUNT_NUMBER_PATTERN)
        assert not compiled.fullmatch(value), f"expected INVALID: {value!r}"
