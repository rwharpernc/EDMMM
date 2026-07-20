#!/usr/bin/env python3
"""
Builds a release-ready copy of the EDMMM plugin into dist/.

Produces:
- dist/EDMMM/            a plain copy of the plugin folder, ready to drop
                          straight into EDMC's plugins directory for testing
- dist/EDMMM-vX.Y.Z.zip   the same folder, zipped, for GitHub Releases

Used both for local "give me a ready to test build" runs and by
.github/workflows/release.yml when a version tag is pushed.
"""
import shutil
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "EDMMM"
DIST_DIR = REPO_ROOT / "dist"
PLUGIN_NAME = "EDMMM"

# Anything in the source folder that shouldn't ship to end users.
EXCLUDE_DIR_NAMES = {"__pycache__", "logs", ".pytest_cache"}
EXCLUDE_FILE_SUFFIXES = (".pyc", ".pyo")


def _ignore(directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDE_DIR_NAMES:
            ignored.add(name)
        elif name.endswith(EXCLUDE_FILE_SUFFIXES):
            ignored.add(name)
    return ignored


def read_version() -> str:
    return (SOURCE_DIR / "version").read_text(encoding="utf8").strip()


def build() -> Path:
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"Plugin source folder not found: {SOURCE_DIR}")

    version = read_version()
    print(f"Building {PLUGIN_NAME} v{version}")

    DIST_DIR.mkdir(exist_ok=True)

    staged_plugin_dir = DIST_DIR / PLUGIN_NAME
    if staged_plugin_dir.exists():
        shutil.rmtree(staged_plugin_dir)
    shutil.copytree(SOURCE_DIR, staged_plugin_dir, ignore=_ignore)
    print(f"  copied plugin folder -> {staged_plugin_dir}")

    zip_path = DIST_DIR / f"{PLUGIN_NAME}-v{version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staged_plugin_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(DIST_DIR))
    print(f"  wrote release zip  -> {zip_path}")

    return zip_path


if __name__ == "__main__":
    build()
