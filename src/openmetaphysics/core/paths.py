"""Path resolution for data that lives outside the Python package.

The repository ships two data trees that are not importable Python packages but
are needed at runtime: ``knowledge/`` (frozen corpora, RAG/Explain) and
``reference/`` (frozen contracts, contract adapters). They must be found in all
supported run modes:

* **source checkout / editable install** -- the data sits next to ``src/``;
* **wheel / plain ``pip install``** -- there is no repository tree, so the data
  comes from ``OM_KNOWLEDGE_DIR`` / ``OM_REFERENCE_DIR`` or, when the wheel
  bundles it, from ``openmetaphysics/data/`` inside the package;
* **Docker** -- the image copies the trees and pins the two ``OM_*`` variables.

Nothing here assumes a fixed index into ``Path.parents``: the repository layout
is found by searching upwards for a marker (``pyproject.toml`` + ``src/``), so
moving or renaming the checkout keeps working. A missing configured directory is
logged as a warning instead of being silently ignored.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from importlib import resources
from pathlib import Path

logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).resolve().parents[1]  # .../openmetaphysics
_KNOWLEDGE_DIR_NAME = "knowledge"
_REFERENCE_DIR_NAME = "reference"


def _configured_dir(setting_name: str) -> Path | None:
    """Value of an ``OM_*`` directory setting, when it points at a directory."""
    from .config import get_settings

    raw = getattr(get_settings(), setting_name, None)
    if not raw:
        return None
    path = Path(str(raw)).expanduser()
    if not path.is_dir():
        logger.warning(
            "OM_%s points to a missing directory: %s (knowledge/contract data will be unavailable)",
            setting_name.upper(),
            path,
        )
        return None
    return path


def packaged_data_dir(*parts: str, package_dir: Path | None = None) -> Path | None:
    """``<package>/data/<parts>`` when the distribution bundles it."""
    base = Path(package_dir) if package_dir is not None else PACKAGE_DIR
    candidate = base.joinpath("data", *parts)
    if candidate.is_dir():
        return candidate
    if package_dir is not None:
        return None
    try:  # zip-safe alternative for unusual importers/lazy loaders
        traversable = resources.files("openmetaphysics").joinpath("data", *parts)
        if traversable.is_dir():
            return Path(str(traversable))
    except Exception:  # pragma: no cover - defensive: weird importers
        return None
    return None


def project_root(start: Path | None = None) -> Path | None:
    """Nearest ancestor that looks like the source checkout, if any."""
    current = (Path(start) if start is not None else Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    return None


def repository_dir(name: str, start: Path | None = None) -> Path | None:
    """A data directory inside the source checkout (``knowledge``/``reference``)."""
    root = project_root(start)
    if root is None:
        return None
    candidate = root / name
    return candidate if candidate.is_dir() else None


def _first_dir(candidates: Iterable[Path | None]) -> Path | None:
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    return None


def knowledge_dir(*, start: Path | None = None, package_dir: Path | None = None) -> Path | None:
    """Resolve the ``knowledge/`` corpus directory (``OM_KNOWLEDGE_DIR`` first)."""
    return _first_dir(
        [
            _configured_dir("knowledge_dir"),
            packaged_data_dir(_KNOWLEDGE_DIR_NAME, package_dir=package_dir),
            repository_dir(_KNOWLEDGE_DIR_NAME, start),
            Path.cwd() / _KNOWLEDGE_DIR_NAME,
        ]
    )


def reference_dir(*, start: Path | None = None, package_dir: Path | None = None) -> Path | None:
    """Resolve the ``reference/`` tree holding the frozen contracts."""
    return _first_dir(
        [
            _configured_dir("reference_dir"),
            packaged_data_dir(_REFERENCE_DIR_NAME, package_dir=package_dir),
            repository_dir(_REFERENCE_DIR_NAME, start),
        ]
    )


def data_path(relative: str, *, reference: bool = False) -> Path:
    """Path for a data file, keeping the classic relative form as a fallback.

    Used for module-level constants: when the directory cannot be resolved
    (neither checkout nor configured nor bundled) the returned path is relative
    to the current working directory, so a later read fails with a clear
    ``FileNotFoundError`` naming the path instead of an obscure ``IndexError``.
    """
    directory = reference_dir() if reference else knowledge_dir()
    if directory is not None:
        return directory / relative
    return Path(relative)


def configured_dir(setting_name: str) -> Path | None:
    """Public wrapper around the ``OM_*`` directory setting lookup."""
    return _configured_dir(setting_name)


# Absolute paths for diagnostics: never assume a repository layout index.
def describe_layout() -> dict[str, str | None]:
    """Human/machine readable resolution result (used by warnings and smoke)."""
    knowledge = knowledge_dir()
    reference = reference_dir()
    root = project_root()
    return {
        "package_dir": str(PACKAGE_DIR),
        "knowledge_dir": str(knowledge) if knowledge else None,
        "reference_dir": str(reference) if reference else None,
        "project_root": str(root) if root else None,
        "cwd": os.getcwd(),
    }


__all__ = [
    "PACKAGE_DIR",
    "configured_dir",
    "packaged_data_dir",
    "project_root",
    "repository_dir",
    "knowledge_dir",
    "reference_dir",
    "data_path",
    "describe_layout",
]
