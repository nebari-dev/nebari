"""a backport for the qhub version references"""

import re

try:
    from importlib.metadata import distribution
except ModuleNotFoundError:
    from importlib_metadata import distribution

__version__ = distribution("qhub").version


def rounded_ver_parse(versionstr):
    """
    Take a package version string and return an int tuple of only (major,minor,patch),
    ignoring and post/dev etc.

    So:
    rounded_ver_parse("0.1.2") returns (0,1,2)
    rounded_ver_parse("0.1.2.dev65+g2de53174") returns (0,1,2)
    rounded_ver_parse("0.1") returns (0,1,0)
    """
    m = re.match(
        "^(?P<major>[0-9]+)(\\.(?P<minor>[0-9]+)(\\.(?P<patch>[0-9]+))?)?", versionstr
    )
    assert m is not None
    major = int(m.group("major") or 0)
    minor = int(m.group("minor") or 0)
    patch = int(m.group("patch") or 0)
    return (major, minor, patch)
