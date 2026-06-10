#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml==6.0.2",
# ]
# ///

"""
Refresh pyodide-recipes-packages.json with the set of PyPI projects that
have a recipe in pyodide/pyodide-recipes.
"""

import datetime
import json
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO_URL = "https://github.com/pyodide/pyodide-recipes"

# These tags mark recipes for libraries (libffi, libyaml, etc.) rather than
# things that show up as PyPI projects, so they're not relevant here.
NOT_PYPI_TAGS = {"shared_library", "static_library", "library"}


def normalize(name: str) -> str:
    # PEP 503 normalisation.
    return re.sub(r"[-_.]+", "-", name).lower()


def pypi_name(meta: dict) -> str:
    about = meta.get("about") or {}
    pypi_url = about.get("PyPI") or about.get("pypi")
    if pypi_url:
        return normalize(pypi_url.rstrip("/").rsplit("/", 1)[-1])
    return normalize(meta["package"]["name"])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth=1",
                "--filter=blob:none",
                "--sparse",
                REPO_URL,
                tmpdir,
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", tmpdir, "sparse-checkout", "set", "packages"],
            check=True,
        )

        packages = set()
        patched_packages = set()
        for meta_file in Path(tmpdir, "packages").glob("*/meta.yaml"):
            meta = yaml.safe_load(meta_file.read_text())
            tags = set((meta.get("package") or {}).get("tag") or [])
            if tags & NOT_PYPI_TAGS:
                continue
            name = pypi_name(meta)
            packages.add(name)
            # A recipe with patches needed pyodide-specific changes to work,
            # as opposed to e.g. just being bundled as a common dependency.
            if (meta.get("source") or {}).get("patches"):
                patched_packages.add(name)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    with open("pyodide-recipes-packages.json", "w") as f:
        json.dump(
            {
                "last_update": now.strftime("%A, %d %B %Y, %X %Z"),
                "packages": sorted(packages),
                "patched_packages": sorted(patched_packages),
            },
            f,
            indent=1,
        )
        f.write("\n")


if __name__ == "__main__":
    main()
