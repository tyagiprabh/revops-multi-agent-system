"""Locate repo files (agent specs, sample data) in both run modes.

Editable installs run from the repo checkout, so repo-root-relative paths
work. A regular install (e.g. the Docker image) puts the package in
site-packages, so we fall back to the current working directory, where the
image copies agents/ and data/samples/.
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_file(*parts: str) -> Path:
    for base in (_REPO_ROOT, Path.cwd()):
        candidate = base.joinpath(*parts)
        if candidate.exists():
            return candidate
    return _REPO_ROOT.joinpath(*parts)
