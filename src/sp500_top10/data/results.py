"""Named stage outputs: numeric tables and separately shaped CSV layouts."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class StageResult:
    tables: dict[str, pd.DataFrame]
    csvs: dict[str, pd.DataFrame] = field(default_factory=dict)
