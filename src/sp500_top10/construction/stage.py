"""Orchestrate construction without notebook execution."""

from ..config import ConstructionConfig
from ..data.results import StageResult
from .output import calculate_output
from .portfolios import calculate_portfolios
from .queries import load_universe_company_universe
from .ranking import calculate_ranking
from .selection import calculate_selection
from .universe import calculate_universe
from .validation import calculate_validation


def run(repository, config: ConstructionConfig) -> StageResult:
    company_universe_input = load_universe_company_universe(repository, config=config)
    (company_universe,) = calculate_universe(company_universe_input, config=config)
    (quarterly_rankings,) = calculate_ranking(company_universe, config=config)
    selected_top10, selected_top20 = calculate_selection(quarterly_rankings, config=config)
    (
        top10_buffered_20_weights,
        top10_equal_weights,
        top10_market_cap_weights,
        top20_market_cap_weights,
    ) = calculate_portfolios(selected_top10, selected_top20, config=config)
    calculate_validation(
        top10_buffered_20_weights,
        top10_equal_weights,
        top10_market_cap_weights,
        top20_market_cap_weights,
        config=config,
    )
    (quarterly_index_weights,) = calculate_output(
        top10_buffered_20_weights,
        top10_equal_weights,
        top10_market_cap_weights,
        top20_market_cap_weights,
        config=config,
    )
    return StageResult(tables={"quarterly_index_weights": quarterly_index_weights}, csvs={})
