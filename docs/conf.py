"""Sphinx configuration for the Extended Data documentation site."""

from __future__ import annotations


project = "Extended Data"
author = "Jon Bogaty"
copyright = "2025-2026, Jon Bogaty"  # noqa: A001

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

source_suffix = {
    ".rst": "restructuredtext",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "Extended Data"
html_static_path = ["_static"]
html_css_files = ["extended-data.css"]
html_extra_path = ["CNAME"]
html_theme_options = {
    "source_repository": "https://github.com/jbcom/extended-data/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#0f766e",
        "color-brand-content": "#115e59",
        "color-api-name": "#1d4ed8",
        "color-api-pre-name": "#374151",
    },
    "dark_css_variables": {
        "color-brand-primary": "#5eead4",
        "color-brand-content": "#99f6e4",
        "color-api-name": "#93c5fd",
        "color-api-pre-name": "#d1d5db",
    },
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

autodoc2_packages = [
    {
        "path": "../src/extended_data",
        "module": "extended_data",
        "exclude_dirs": ["__pycache__"],
    }
]
autodoc2_render_plugin = "rst"
autodoc2_docstring_parser_regexes = [(r".*", "myst")]
autodoc2_hidden_objects = ["inherited", "dunder"]
autodoc2_class_docstring = "merge"
autodoc2_module_summary = True
