"""a backport for the qhub version references"""
try:
    from importlib.metadata import distribution
except ModuleNotFoundError:
    from importlib_metadata import distribution

__version__ = distribution("qhub").version
