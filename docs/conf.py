# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import version
import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
import xrdimageutil as xiu

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

html_static_path = ["_static"]
html_theme = "pydata_sphinx_theme"
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'
html_theme_options = {
    'show_prev_next': False,
    'navbar_align': 'left',
    'github_url': 'https://github.com/myusername/my-project',
    'navbar_links': [
        ('API', 'api'),
        ('Examples', 'examples'),
    ],
}

html_baseurl = '/xrd-image-util/'
