import pytest

from tests.common.run_notebook import assert_match_output


@pytest.mark.parametrize(
    "expected, actual, exact",
    [
        ("success: 6", "success: 6", True),
        ("success: 6", "success", False),
        ("6", "6", True),
        ("abcde", "cde", False),
    ],
)
def test_output_match(expected, actual, exact):
    assert_match_output(expected, actual, exact_match=exact)


@pytest.mark.parametrize(
    "expected, actual, exact",
    [
        ("True", "False", True),
        ("success: 6", "success", True),
        ("60", "6", True),
        ("abcde", "cde", True),
    ],
)
def test_output_not_match(expected, actual, exact):
    msg = f"Expected output: {expected} not found in actual output: {actual}"
    with pytest.raises(AssertionError, match=msg):
        assert_match_output(expected, actual, exact_match=exact)
