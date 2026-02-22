from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("odmlib")
except PackageNotFoundError:
    __version__ = "0.2.0.dev"