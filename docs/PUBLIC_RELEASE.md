# Public release scope

The shared repository contains the research application and a deterministic synthetic demonstration. Historical source data, prepared research databases, and private reference material remain local.

## Included in the repository

- Python package, entry point, packaged SQL queries, and dependency specifications.
- Methodology, architecture, output contracts, and verification documentation.
- Calculation, provider, and operational tests, plus the GitHub Actions workflow.
- Fictional-data generator and an optional exploration notebook without saved outputs.
- Operational tools for provider snapshots, export recovery, and comparison with a locally held private reference.

The synthetic demonstration runs without licensed inputs or network access. Historical reproduction requires a compatible prepared source database and, for offline operation, a recorded provider snapshot. These inputs are not distributed with the code.

## Local-only material

The ignore rules exclude source and result databases, original research notebooks, raw data, generated outputs, caches, logs, environments, backups, credentials files, and private reference directories.

The migration checkpoints, relocation notes, and reference-freezing helper are also retained locally and excluded from version control. They are not required to install the application or run the synthetic demonstration.

Calculated reports and research presentations may be added deliberately after reviewing their contents and applicable sharing permissions. Generated output directories are excluded by default.

## Before sharing an update

Review the staged file list and diff, keep notebook outputs and attachments clear, and run the checks appropriate to the change. Application changes should pass the automated checks and synthetic workflow described in the [README](../README.md#quality-and-validation).

Ignore rules do not remove files already tracked by Git or erase earlier commits. Untracking a file while keeping its local copy excludes it from subsequent commits; its previous versions remain in repository history.
