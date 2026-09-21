# S&P 500 Top 10 research pipeline

A local Python application for concentrated-index construction, daily backtesting, performance analysis, and factor attribution. Production code covers the responsibilities of the original notebooks 03–07. It preserves the existing methodology and the 38 CSV report contracts.

## Run from Git Bash

In this existing workspace, activate the existing environment in this project folder:

```bash
source .venv/Scripts/activate
python run.py --offline
```

The offline command reproduces calculations using the recorded local provider snapshot. For a complete run that refreshes Yahoo, FRED, and Fama–French inputs, use:

```bash
python run.py
```

Online refreshes can change the input data as providers revise history. Compatibility checks use the frozen offline inputs, so they do not confuse a source-data revision with a code change.

Run a single stage only when its upstream results exist and match the current code, settings, and data:

```bash
python run.py --stage construction
python run.py --stage backtesting
python run.py --stage market-data --offline
python run.py --stage analytics
python run.py --stage factor-attribution
```

Run records are saved after each stage and on errors. A failed process returns a nonzero exit code. If a prerequisite is reported stale, rerun the affected upstream stages or the complete workflow.

## Input and output locations

| Purpose | Portable default |
|---|---|
| Private source database | `data/sp500.duckdb` |
| Calculated result database | `data/sp500_results.duckdb` |
| Analytics CSVs | `outputs/analytics/` |
| Factor-attribution CSVs | `outputs/factor_attribution/` |
| Normalized offline provider snapshot | `cache/market_data/` |
| New provider payloads | `cache/raw/` |
| Run manifests | `logs/` |

All relative paths resolve against the project folder, even when called from another directory. SQL resources load from the Python package. The input database is attached read-only; the application refuses to use it as the result database.

The project now runs directly from the repository root. The ignored `.local/paths.json` uses the portable defaults above. The original source remains `data/sp500.duckdb`; calculated results use the separate `data/sp500_results.duckdb`. Pre-move files and output checksums are recorded privately under `.private/relocation-20260921/`.

Environment variables override the path defaults and local profile:

```bash
export SP500_SOURCE_DB="C:/path/to/private/sp500.duckdb"
export SP500_OUTPUT_ROOT="outputs"
python run.py --offline
```

Also supported: `SP500_RESULTS_DB`, `SP500_CACHE_ROOT`, and `SP500_LOG_ROOT`. Use Windows-compatible absolute paths on Windows, or project-relative paths.

The source schema is described in [the architecture](docs/ARCHITECTURE.md). The original database is not distributed. Exact CSV filenames and ordered headers are in [the output contract](docs/CSV_OUTPUT_CONTRACT.md).

## Move the project

1. Move or copy the project code and whichever ignored local `data/`, `cache/`, and `outputs/` folders you want to retain.
2. Remove or update `.local/paths.json` if it still refers to the former parent directory. If the source database remains elsewhere, set `SP500_SOURCE_DB` to that location.
3. Recreate the environment at the destination. Virtual environments and editable-install paths should not be moved as portable artifacts.

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements-lock.txt
python -m pip install -e '.[dev]'
python run.py --offline
```

The tested baseline is Python 3.13.5 on Windows. The lock records the original environment. The package declares direct runtime dependencies separately in `pyproject.toml`.

## Central configuration

Edit calculation defaults in `src/sp500_top10/config.py`. Settings are grouped into construction, backtesting, market data, analytics, and factor attribution. Configuration objects are frozen dataclasses; functions receive settings explicitly. Paths are resolved by `load_config()` and are not embedded in calculation modules.

The compatible report set supports Top 10 market-cap, equal-weight, and buffered-cap portfolios, plus Top 20 market-cap. Arbitrary new strategies are not part of this first version. If changing dates, update the relevant snapshot labels and historical episode definitions as well; unavailable required dates intentionally fail validation.

The code preserves price-based weight drift, next-trading-day quarterly implementation, month-end breach review, current turnover and cost conventions, each analysis's sample restrictions, and the existing factor-regression definitions. Known original behavior, including the legacy monthly-reset count label mismatch, is retained for a separate later review.

## Synthetic demonstration

Create deterministic fictional input data and provider snapshots without downloading anything:

```bash
python examples/create_synthetic.py --destination .local/synthetic
python run.py --root .local/synthetic --offline
```

The full demo produces the same set of table and CSV schemas. Its values are fictional and are not backtest evidence. The generator refuses to overwrite an existing source file; choose a new destination for another demo.

## Tests and private compatibility checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
ruff check src run.py tools examples tests
ruff format --check src run.py tools examples tests
```

Tests cover independent numerical examples, source protection, write rollback, output rollback, lineage checks, provider parsing, and moving the code into a differently named directory. CI uses synthetic data only.

See [completed migration verification](docs/VERIFICATION.md) for the results and limits of the local checks.

The private baseline is stored under `.private/reference/`. To compare your calculated results with it:

```bash
python tools/verify_compatibility.py
```

This checks all 50 result tables, all 38 CSVs, exact schemas, row/column order for CSVs, numerical equivalence at absolute/relative tolerance 1e-12, and unchanged original notebooks and source. Reports are saved under `.private/verification/`. This tool intentionally requires the private baseline and original notebooks; the production runner does not.

For a different source database already containing the six provider tables, explicitly record a normalized offline snapshot:

```bash
python tools/capture_market_snapshot.py --source "C:/path/to/database.duckdb"
```

The tool refuses to overwrite an existing snapshot. The provenance distinguishes normalized tables captured from a database from newly downloaded provider payloads.

## Checkpoints and publication recovery

Code is saved as ordinary files. [Implementation progress](docs/IMPLEMENTATION_PROGRESS.md) records migration checkpoints. Every runtime stage saves a local manifest and a transactionally persisted result set. Stored lineage includes source and code fingerprints and actual upstream table identities.

CSV sets are validated in `.publication/` beneath their output directory before replacement. A completion marker is written last. An interrupted publication remains marked incomplete and blocks another publication until recovered. Retained backups allow restoration; no claim is made that multiple file replacements are one atomic filesystem operation.

The original notebooks, `.private/`, `.local/`, databases, caches, logs, and generated outputs are ignored by Git. No GitHub publication is performed by the application. See [public release notes](docs/PUBLIC_RELEASE.md) before assembling the eventual public repository.

To restore the previous CSV set after an interrupted publication, run `python tools/recover_csv_publication.py outputs/analytics` (or `outputs/factor_attribution`), then rerun the affected stage.

## Exploration

The optional [exploration notebook](notebooks/exploration.ipynb) imports the same package and reads calculated results. Review and clear locally saved outputs before publishing it; execution can save results or tracebacks. Production execution never reads or executes a notebook.

## Repository-root relocation

See [relocation verification](docs/RELOCATION.md) for preservation checks, the Git history review, and the current review-before-push status.
