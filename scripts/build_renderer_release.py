"""Build a cleaned Renderer release archive.

The archive is written to ``dist/Renderer.zip`` and contains the package
under a top-level ``Renderer`` directory.
"""

from __future__ import annotations

import zipfile
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = PACKAGE_DIR.parent / "dist"
ARCHIVE_PATH = DIST_DIR / "Renderer.zip"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "scripts",
    "tests",
    "versions",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def should_skip(path: Path) -> bool:
    """Return whether a path should be excluded from the release package."""
    relative_parts = path.relative_to(PACKAGE_DIR).parts
    if set(relative_parts) & EXCLUDED_DIR_NAMES:
        return True
    return path.suffix.lower() in EXCLUDED_SUFFIXES


def build_archive() -> Path:
    """Create the Renderer release archive and return its path."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    with zipfile.ZipFile(ARCHIVE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in PACKAGE_DIR.rglob("*"):
            if source.is_dir() or should_skip(source):
                continue
            arcname = Path("Renderer") / source.relative_to(PACKAGE_DIR)
            archive.write(source, arcname.as_posix())

    return ARCHIVE_PATH


def main() -> None:
    """Build the final Renderer release archive."""
    if not PACKAGE_DIR.exists():
        raise FileNotFoundError(f"Renderer package not found: {PACKAGE_DIR}")

    archive_path = build_archive()
    print(f"Release archive: {archive_path}")


if __name__ == "__main__":
    main()
