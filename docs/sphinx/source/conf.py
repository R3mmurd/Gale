"""
Sphinx configuration for the Gale documentation site.
"""

import pathlib
import re
import sys

_repo_root = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))

_pyproject_text = (_repo_root / "pyproject.toml").read_text()
_version_match = re.search(r'^version = "([^"]+)"', _pyproject_text, re.MULTILINE)

project = "Gale"
copyright = "2021-2026, Alejandro Mujica"
author = "Alejandro Mujica"
release = _version_match.group(1)
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = f"Gale {version} documentation"

html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
}

html_context = {
    "display_github": True,
    "github_user": "R3mmurd",
    "github_repo": "Gale",
    "github_version": "main",
    "conf_py_path": "/docs/sphinx/source/",
}

# -- Autodoc -------------------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
