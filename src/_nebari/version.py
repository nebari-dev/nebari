"""a backport for the nebari version references."""

from packaging.version import Version
from importlib.metadata import distribution

__version__ = distribution("nebari").version


def rounded_ver_parse(version: str) -> Version:
    """
    Rounds a version string to the nearest patch version.

    Parameters
    ----------
    version : str
        A version string.

    Returns
    -------
    packaging.version.Version
        A version object.
    """
    base_version = Version(version).base_version
    return Version(base_version)
