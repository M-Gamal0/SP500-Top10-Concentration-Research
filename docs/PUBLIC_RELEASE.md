# Public release preparation

No repository has been published, pushed, or committed as part of this implementation.

The production project now occupies the existing repository root. The relocation review found one reachable commit containing only `.gitignore` and empty README and requirements files; no data or notebooks were present in that history. A `.gitignore` does not remove material already committed. Review all future staged files before each commit. Nothing was staged, committed, or pushed during relocation. See `RELOCATION.md`.

Include the Python package, entry file, dependency specifications, documentation, synthetic generator, tests, and optional exploration notebook. The original notebooks at the project root may contain private source access and saved records and are ignored. Notebooks 01, 02, and 08 are outside the converted production scope.

Do not include the private source or result databases, `.private/`, `.migration/`, `.local/`, caches, logs, environments, generated build folders, or entire output directories by default. Selected calculated reports can be added deliberately later.

Before publishing, verify the actual tracked file list and history in the destination repository and run the synthetic workflow and tests. This is a release step, not something the application performs automatically.
