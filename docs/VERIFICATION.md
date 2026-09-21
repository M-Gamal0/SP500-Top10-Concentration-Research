# Migration verification

Local verification date: 2026-09-21. Runtime: existing Python 3.13.5 virtual environment, invoked through Git Bash on Windows. No GitHub publication was performed.

## Preserved reference

The private reference contains the source database, all eight original notebooks, the original environment versions, and 39 pre-existing CSV files. The contractual production registry has 38 CSVs; the additional historical file remains preserved in the reference. Production writes to a separate database and separate output directories. The source database and original notebooks retain their SHA-256 checksums.

Compatibility was established by running the extracted calculations against the fixed source inputs and normalized provider snapshot, then comparing every generated table and contractual CSV with existing results. The original notebooks were not re-executed against the source database. This proves equivalence to those saved results; it is not a new independent assessment of the research methodology.

## Results

| Stage | Matching tables | Matching CSVs |
|---|---:|---:|
| Construction | 1 | 0 |
| Backtesting | 5 | 0 |
| Market data, recorded snapshot | 6 | 0 |
| Analytics | 28 | 28 |
| Factor attribution | 10 | 10 |
| Total | 50 | 38 |

Table schemas, identifiers, dates, labels, CSV column ordering, and CSV row ordering match. Floating-point values use `atol=1e-12, rtol=1e-12`: the permitted difference is an absolute floor plus a relative allowance proportional to the reference value. Internal tables are sorted before comparison; physical database row order is not treated as a contract.

Thirty-seven CSVs are byte-identical. `top10_concentration_monthly.csv` has very small floating-point differences in market-cap sums and the shares derived from them. In the recorded comparison, the maximum absolute differences were approximately 3.36e-8 for total market capitalization, 3.06e-16 for the market-cap share, and 3.20e-14 for its percentage representation. All satisfy the stated combined tolerance. These differences are consistent with floating-point aggregation order; no rounding or formula was changed to force a match. Private comparison records and numerical diagnostics are in `.private/verification/`.

## Other checks

- Seventeen independent calculation, provider-parser, and operational tests pass.
- A complete deterministic fictional-data run produces all stages without paid inputs or provider requests.
- Relocation to a directory containing spaces works when launched from an unrelated working directory.
- The source attachment rejects writes. Failed database writes roll back; CSV replacement errors restore prior output; interrupted CSV publication has an explicit recovery tool.
- Prerequisite validation rejects modified result tables; offline snapshots reject checksum corruption.
- The wheel builds and imports independently of the checkout, including all 30 SQL resources.
- Ruff lint and formatting checks cover all 94 Python files.
- The final complete run is recorded locally as `logs/20260921T150025-86a8d8e3.json`. Subsequent independent factor attribution completed as `logs/20260921T150216-77763d79.json`, confirming continuation with the stored prerequisites.

The original monthly-reset counter label mismatch remains preserved, as required by the architecture. The optional exploration notebook contains no saved output. `CSV_OUTPUT_CONTRACT.md` was preserved unchanged; its original status line describes the pre-migration inventory, while this document records completed verification.

## Limits and release status

Online adapters were checked with controlled responses, including retries, parsing, download options, and raw-input recording. A live Yahoo/FRED/Fama–French refresh was not performed as part of the final compatibility run; provider revisions would change the inputs. Use `python run.py --offline` to reproduce the verified local snapshot and `python run.py` to request a fresh online run.

CI configuration is prepared for Windows and Linux with synthetic data. Remote CI has not run because the project has not been published. Review destination repository contents and history separately before a future public release.
