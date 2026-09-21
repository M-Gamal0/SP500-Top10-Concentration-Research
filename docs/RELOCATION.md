# Repository-root relocation

Status: relocated and verified. Only deletion of the empty old directory remains: Windows reports that another process has it open.

The existing `.venv`, source database, original notebooks, saved outputs, frozen references, and CSV output contract are preserved. The local path override was reset to portable defaults. All 1,606 original files were hash-verified after copying. Versions changed by path updates or the validation rerun are preserved under `.private/relocation-20260921/original-versions/` or `before-path-updates/`. The old directory is now empty. All nine pre-existing parent data files retained their SHA-256 checksums; the existing environment file inventory retained sizes and modification times.

Git review: one reachable commit (`f65b7be`), containing `.gitignore` and empty README and requirements files. All reflog entries refer to the same commit. No private data or notebooks were found in this history. The index was unchanged and empty of staged changes. The previously deleted `requirements.txt` remains deleted; runtime dependencies are declared in `pyproject.toml` and `requirements-lock.txt`.

The original eight research notebooks remain local and ignored. The exploration notebook retains its user-saved missing-environment-variable traceback; clear its outputs after review before publishing. From Git Bash, use `export SP500_PROJECT_ROOT="$(pwd -W)"` before launching the notebook environment.

No staging, commits, history changes, or pushes were performed.

## Completed checks

The relocated offline workflow completed as `logs/20260921T154937-30df7b3d.json`. All 50 tables and 38 CSVs match the frozen reference; 37 CSVs are byte-identical. All 17 tests pass. Ruff lint and formatting pass for all 94 Python files. Original notebooks, source database, and CSV contract remain unchanged.

## Remaining empty-directory cleanup

Close terminals and editor/workspace views using the old subfolder, then run `rmdir SP500-Top10-AI-Assisted` from the repository root in Git Bash. This command removes an empty directory only. The production project already runs from the repository root and does not depend on that directory.
