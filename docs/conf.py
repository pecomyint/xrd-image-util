# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

gh_org = "henryjsmith12"
project = "xrd-image-util"
copyright = "2023, Henry Smith"
author = "Henry Smith"

extensions = """
    sphinx.ext.autodoc
    sphinx.ext.autosummary
    sphinx.ext.coverage
    sphinx.ext.githubpages
    sphinx.ext.inheritance_diagram
    sphinx.ext.mathjax
    sphinx.ext.todo
    sphinx.ext.viewcode
""".split()

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "pydata_sphinx_theme"
html_baseurl = '/xrd-image-util/'
html_theme_options = {
    'navbar_align': 'left',
    'show_toc_level': 1,
}
html_sidebars = {
    "**": ["index.rst", "getting_started.rst"]
}
