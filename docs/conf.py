# Configuration file for the Sphinx documentation builder.

from pathlib import Path
import sys

HERE = Path(__file__).parent

# -- Project information -----------------------------------------------------

project = "QHub"
copyright = "2021, Quansight"
author = "Quansight"

# The short X.Y version
# version = re.match(r"^([0-9]+\.[0-9]+).*", release).group(1)


# -- General configuration ---------------------------------------------------

BLOG_TITLE = title = html_title = "Docs"
BLOG_AUTHOR = author = "Quansight"
html_theme = "pydata_sphinx_theme"
html_sidebars = {
    "**": ["announcement", "search-field", "sidebar-nav-bs", "sidebar-ethical-ads"],
}

# The master toctree document.
master_doc = "index"

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ".md .rst .ipynb .py".split()

# To find the local substitute extension
sys.path.append(str(HERE / "ext"))

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "substitute",
]

# autoapi.extension
autoapi_type = "python"
autoapi_dirs = ()

THEME = "material-theme"
DEFAULT_LANG = "en"

NAVIGATION_LINKS = {
    DEFAULT_LANG: tuple(),
}

THEME_COLOR = "4f28a8"  # "#7B699F"

POSTS = (
    ("posts/*.md", "posts", "post.tmpl"),
    ("posts/*.rst", "posts", "post.tmpl"),
    ("posts/*.txt", "posts", "post.tmpl"),
    ("posts/*.html", "posts", "post.tmpl"),
    ("posts/*.ipynb", "posts", "post.tmpl"),
    ("posts/*.md.ipynb", "posts", "post.tmpl"),
)

templates_path = ["_templates"]


html_logo = "source/images/qhub_logo.png"

# exclude build directory and Jupyter backup files:
exclude_patterns = [
    ".nox",
    "_build",
    "*checkpoint*",
    "site",
    "jupyter_execute",
    "conf.py",
    "README.md",
    "ext",
]

latex_documents = [
    (
        master_doc,
        "qhub.tex",
        "Infrastructure as Code",
        "QHub",
        "manual",
    )
]
nitpicky = True
jupyter_execute_notebooks = "off"

myst_update_mathjax = False
# Generate heading anchors for heading levels <h[1-3]>
myst_heading_anchors = 5

# Import qhub version number
__version__ = None
exec(open(HERE.parent / "nebari" / "version.py").read())

qhub_version_string = __version__

# SITE_URL = "https://quansight.github.io/qhub-home/"
