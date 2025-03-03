import sys

import pytest

from _nebari.utils import (
    JsonDiff,
    JsonDiffEnum,
    byte_unit_conversion,
    deep_merge,
    run_subprocess_cmd,
)


@pytest.mark.parametrize(
    "value, from_unit, to_unit, expected",
    [
        (1, "", "B", 1),
        (1, "B", "B", 1),
        (1, "KB", "B", 1000),
        (1, "K", "B", 1000),
        (1, "k", "b", 1000),
        (1, "MB", "B", 1000**2),
        (1, "GB", "B", 1000**3),
        (1, "TB", "B", 1000**4),
        (1, "KiB", "B", 1024),
        (1, "MiB", "B", 1024**2),
        (1, "GiB", "B", 1024**3),
        (1, "TiB", "B", 1024**4),
        (1000, "B", "KB", 1),
        (1000, "KB", "K", 1000),
        (1000, "K", "KB", 1000),
        (1000, "MB", "KB", 1000**2),
        (1000, "GB", "KB", 1000**3),
        (1000, "TB", "KB", 1000**4),
        (1000, "KiB", "KB", 1024),
        (1000, "Ki", "KB", 1024),
        (1000, "Ki", "K", 1024),
        (1000, "MiB", "KB", 1024**2),
        (1000, "GiB", "KB", 1024**3),
        (1000, "TiB", "KB", 1024**4),
        (1000**2, "B", "MB", 1),
        (1000**2, "KB", "MB", 1000),
        (1000**2, "MB", "MB", 1000**2),
        (1000**2, "GB", "MB", 1000**3),
        (1000**2, "TB", "MB", 1000**4),
        (1000**2, "MiB", "MB", 1024**2),
        (1000**3, "B", "GB", 1),
        (1000**3, "KB", "GB", 1000),
    ],
)
def test_byte_unit_conversion(value, from_unit, to_unit, expected):
    assert byte_unit_conversion(f"{value} {from_unit}", to_unit) == expected


def test_JsonDiff_diff():
    obj1 = {"a": 1, "b": {"c": 2, "d": 3}}
    obj2 = {"a": 1, "b": {"c": 3, "e": 4}, "f": 5}
    diff = JsonDiff(obj1, obj2)
    assert diff.diff == {
        "b": {
            "e": {JsonDiffEnum.ADDED: 4},
            "c": {JsonDiffEnum.MODIFIED: (2, 3)},
            "d": {JsonDiffEnum.REMOVED: 3},
        },
        "f": {JsonDiffEnum.ADDED: 5},
    }


def test_JsonDiff_modified():
    obj1 = {"a": 1, "b": {"!": 2, "-": 3}, "+": 4}
    obj2 = {"a": 1, "b": {"!": 3, "+": 4}, "+": 5}
    diff = JsonDiff(obj1, obj2)
    modifieds = diff.modified()
    assert sorted(modifieds) == sorted([(["b", "!"], 2, 3), (["+"], 4, 5)])


def test_deep_merge_order_preservation_dict():
    value_1 = {
        "a": [1, 2],
        "b": {"c": 1, "z": [5, 6]},
        "e": {"f": {"g": {}}},
        "m": 1,
    }

    value_2 = {
        "a": [3, 4],
        "b": {"d": 2, "z": [7]},
        "e": {"f": {"h": 1}},
        "m": [1],
    }

    expected_result = {
        "a": [1, 2, 3, 4],
        "b": {"c": 1, "z": [5, 6, 7], "d": 2},
        "e": {"f": {"g": {}, "h": 1}},
        "m": 1,
    }

    result = deep_merge(value_1, value_2)
    assert result == expected_result
    assert list(result.keys()) == list(expected_result.keys())
    assert list(result["b"].keys()) == list(expected_result["b"].keys())
    assert list(result["e"]["f"].keys()) == list(expected_result["e"]["f"].keys())


def test_deep_merge_order_preservation_list():
    value_1 = {
        "a": [1, 2],
        "b": {"c": 1, "z": [5, 6]},
    }

    value_2 = {
        "a": [3, 4],
        "b": {"d": 2, "z": [7]},
    }

    expected_result = {
        "a": [1, 2, 3, 4],
        "b": {"c": 1, "z": [5, 6, 7], "d": 2},
    }

    result = deep_merge(value_1, value_2)
    assert result == expected_result
    assert result["a"] == expected_result["a"]
    assert result["b"]["z"] == expected_result["b"]["z"]


def test_deep_merge_single_dict():
    value_1 = {
        "a": [1, 2],
        "b": {"c": 1, "z": [5, 6]},
    }

    expected_result = value_1

    result = deep_merge(value_1)
    assert result == expected_result
    assert list(result.keys()) == list(expected_result.keys())
    assert list(result["b"].keys()) == list(expected_result["b"].keys())


def test_deep_merge_empty():
    expected_result = {}

    result = deep_merge()
    assert result == expected_result


size_kb_end_args = [
    (1, ""),  # 1KB no newline
    (1, "\\n"),  # 1KB with newline
    (64, ""),  # 64KB no newline
    (64, "\\n"),  # 64KB with newline
    (128, ""),  # 128KB no newline
    (128, "\\n"),  # 128KB with newline
]


@pytest.mark.parametrize(
    "size_kb,end",
    size_kb_end_args,
    ids=[
        f"{params[0]}KB{'_newline' if params[1] else ''}" for params in size_kb_end_args
    ],
)
def test_run_subprocess_cmd(size_kb, end):
    """Test large output handling using current Python interpreter"""
    python_exe = sys.executable
    command = [python_exe, "-c", f"print('a' * {size_kb} * 1024, end='{end}')"]

    exit_code, output = run_subprocess_cmd(
        command, capture_output=True, strip_errors=True, timeout=1
    )
    assert exit_code == 0
    assert len(output.decode()) == size_kb * 1024 + (1 if end else 0)
