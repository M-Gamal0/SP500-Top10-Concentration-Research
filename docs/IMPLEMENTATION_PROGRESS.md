# Implementation checkpoints

Files are saved after each step. This record is updated as verification completes.

## Scope

Production conversion covers notebooks 03–07. Original notebooks and the source database remain unchanged. The methodology and 38 CSV contracts are preserved. No GitHub publication is authorized.

## Current status

- Architecture and output contract read.
- Git Bash and the existing Python 3.13 environment confirmed.
- Local data and migration work excluded by project `.gitignore`.
- Private reference saved: source database copy verified by SHA-256, eight notebook copies, environment versions, and 39 pre-existing CSVs. The production registry includes 38; the additional existing file is preserved only as reference.
- Foundation saved: portable runner and configuration, read-only source attachment, separate result database, transactional writes, run manifests, and explicit output registry.
- Construction verified: all 5,550 rows and the target-table schema match the frozen reference at absolute/relative tolerance 1e-12. Original database and notebooks remain byte-identical.
- Backtesting verified: all five tables match, including the daily weights, rebalance timing, monthly review log, and turnover.
- Market data verified: six normalized provider tables match the fixed offline snapshot. No external refresh was used for compatibility comparison.
- Analytics verified: 28 tables and 28 CSVs match at 1e-12 absolute/relative tolerance; 27 CSVs are byte-identical.
- Factor attribution verified: 10 tables and all 10 CSVs match; all 10 CSVs are byte-identical.
- The concentration CSV has only floating-point aggregation/serialization differences satisfying the combined absolute/relative 1e-12 comparison. Its maximum share difference was 3.06e-16. No methodology change was made.
- Seventeen calculation, provider, and operational tests pass, including relocation to a path with spaces, read-only source protection, transaction rollback, CSV rollback and interrupted-publication recovery, modified upstream results, and corrupted provider snapshots.
- Full offline workflow verified against all 50 tables and 38 CSVs. All original database and notebook checksums remain unchanged; 37 CSVs are byte-identical.
- Full fictional-data workflow completed without private inputs or external requests. The package wheel builds and imports from an unrelated directory, including all 30 SQL resources. Formatting and lint pass for all 94 Python files.
- Final full run after formatting passed all comparisons; factor attribution also completed independently with current prerequisite validation. Implementation and local verification are complete. Live provider refreshes were not used for migration equivalence.

## Local resume commands

Activate the existing environment in Git Bash, then use `python run.py --stage STAGE` and `python tools/verify_compatibility.py --stage STAGE`.

After repository-root relocation, `.local/paths.json` is empty and the source resolves to `data/sp500.duckdb`. New results use this project's `data/` and `outputs/`. The explicit offline provider snapshot is under `cache/market_data/`; it contains normalized provider tables from the frozen reference and records that provenance.

Private stage comparison records are saved in `.private/verification/`. Run status is saved in `logs/` after every stage and on failure. These files are excluded from Git.

## Repository-root relocation

All 1,606 files were copied and hash-verified before path updates. Original data and environment inventories are saved privately. Full parent-folder validation passed (50 tables, 38 CSVs, 17 tests, lint and formatting). All old folder contents were safely removed; Windows still holds the empty directory open. See the final cleanup command in `RELOCATION.md`. See `RELOCATION.md`.
