"""Load SQL relative to the installed package, independent of working directory."""

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=None)
def read_sql(name: str) -> str:
    if "/" in name or "\\" in name or not name.endswith(".sql"):
        raise ValueError("Invalid SQL resource name.")
    return files("sp500_top10").joinpath("data", "sql", name).read_text(encoding="utf-8")
