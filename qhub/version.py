"""a backport for the qhub version references"""
from ast import Mod


try:
    from importlib.metadata import distribution
except ModuleNotFoundError:
    from importlib_metadata import distribution

__version__ = distribution("qhub").version
