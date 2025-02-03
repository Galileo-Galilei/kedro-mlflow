# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
from kedro_mlflow import __version__ as km_version

project = "kedro-mlflow"
copyright = "2020, Yolan Honoré-Rougé"
author = "Yolan Honoré-Rougé"

# The full version, including alpha/beta/rc tags
release = km_version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_click",
    # "sphinx_autodoc_typehints",
    # "sphinx.ext.doctest",
    # "sphinx.ext.todo",
    # "sphinx.ext.coverage",
    # "sphinx.ext.mathjax",
    # "sphinx.ext.ifconfig",
    # "sphinx.ext.viewcode",
    # "nbsphinx",
    "sphinx_design",  # responsive web component support
    "sphinx_copybutton",
    "sphinx_markdown_tables",
    "myst_parser",
]

myst_enable_extensions = ["colon_fence"]

# enable autosummary plugin (table of contents for modules/classes/class
# methods)
autosummary_generate = True
autosummary_generate_overwrite = False
napoleon_include_init_with_doc = True

# enable documentation in markdown
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build"]


# -- Options for HTML output -------------------------------------------------
# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "pydata_sphinx_theme"  # see: https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html

# useful to create dropdown with the name of the directory as the section name
# see https://stackoverflow.com/questions/36925871/toctree-nested-drop-down:
html_theme_options = {
    "logo": {
        "image_light": "source/imgs/logo.png",
        "image_dark": "source/imgs/logo.png",
    },
    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/header-links.html#fontawesome-icons
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/Galileo-Galilei/kedro-mlflow",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/kedro-mlflow/",
            "icon": "fa-brands fa-python",
        },
        {
            "name": "Slack",
            "url": "https://kedro-org.slack.com/",
            "icon": "fa-brands fa-slack",
        },
    ],
    "navbar_start": ["navbar-logo"],
    "navbar_align": "content",
    "header_links_before_dropdown": 5,
    "secondary_sidebar_items": ["page-toc", "edit-this-page", "sourcelink"],
    "use_edit_page_button": True,
}
html_context = {
    "github_user": "Galileo-Galilei",
    "github_repo": "kedro-mlflow",
    "github_version": "master",
    "doc_path": "docs/",  # why not "docs/source/"?
    "default_mode": "light",
}
html_sidebars = {"index": []}


myst_heading_anchors = 5
