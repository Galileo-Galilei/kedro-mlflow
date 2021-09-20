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


from recommonmark.transform import AutoStructify

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
    "recommonmark",
    "sphinx_copybutton",
    "sphinx_markdown_tables",
]

# enable autosummary plugin (table of contents for modules/classes/class
# methods)
autosummary_generate = True
autosummary_generate_overwrite = False
napoleon_include_init_with_doc = True

# enable documentation in markdown
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# useful to create dropdown with the name of the directory as the section name
# see https://stackoverflow.com/questions/36925871/toctree-nested-drop-down:
html_theme_options = {"collapse_navigation": False}


def setup(app):
    # enable rendering RST tables in Markdown
    app.add_config_value("recommonmark_config", {"enable_eval_rst": True}, True)
    app.add_transform(AutoStructify)
