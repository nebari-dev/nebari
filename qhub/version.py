"""a backport for the qhub version references"""
from importlib.metadata import distribution

__version__ = distribution("qhub").version
