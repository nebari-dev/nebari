"""Tests that enforce code conventions across the nebari codebase."""

import importlib
import pkgutil
import types
import typing
from typing import Union, get_args, get_origin

import pydantic
import pytest


def _import_all_nebari_modules():
    """Import all modules under nebari and _nebari packages."""
    for package_name in ("nebari", "_nebari"):
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            continue
        if not hasattr(package, "__path__"):
            continue
        for _importer, modname, _ispkg in pkgutil.walk_packages(
            package.__path__, prefix=package.__name__ + ".", onerror=lambda _name: None
        ):
            try:
                importlib.import_module(modname)
            except Exception:
                pass


def _collect_nebari_models():
    """Recursively collect all pydantic BaseModel subclasses owned by nebari."""
    seen = set()
    result = []

    def _walk(cls):
        for sub in cls.__subclasses__():
            if id(sub) in seen:
                continue
            seen.add(id(sub))
            mod = getattr(sub, "__module__", "") or ""
            if mod.startswith("nebari") or mod.startswith("_nebari"):
                result.append(sub)
            _walk(sub)

    _walk(pydantic.BaseModel)
    return result


def _annotation_allows_none(annotation) -> bool:
    """Check whether a type annotation includes NoneType."""
    if annotation is type(None):
        return True

    origin = get_origin(annotation)

    # typing.Annotated -- unwrap and check the inner type
    if origin is typing.Annotated:
        args = get_args(annotation)
        if args:
            return _annotation_allows_none(args[0])
        return False

    # typing.Union or T | None (types.UnionType in 3.10+)
    if origin is Union or isinstance(annotation, types.UnionType):
        return any(_annotation_allows_none(arg) for arg in get_args(annotation))

    return False


def test_none_default_fields_have_optional_annotation():
    """Every Pydantic field that defaults to None must include None in its type.

    Without an explicit Optional (or Union with None), Pydantic may silently
    coerce None into the declared type at validation time, and static type
    checkers cannot detect the mismatch.
    """
    _import_all_nebari_modules()
    models = _collect_nebari_models()
    assert models, "No nebari BaseModel subclasses found -- import may have failed"

    violations = []
    for model in models:
        for field_name, field_info in model.model_fields.items():
            if field_info.default is None:
                annotation = field_info.annotation
                if annotation is not None and not _annotation_allows_none(annotation):
                    violations.append(
                        f"  {model.__module__}.{model.__qualname__}.{field_name}: "
                        f"defaults to None but annotation is {annotation!r}"
                    )

    if violations:
        msg = (
            "Fields that default to None must use Optional[T], T | None, "
            "or Union[T, None]:\n" + "\n".join(sorted(violations))
        )
        pytest.fail(msg)
