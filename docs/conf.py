# Configuration file for the Sphinx documentation builder.

# import re
# from qhub import __version__ as release

# -- Project information -----------------------------------------------------

project = "QHub"
copyright = "2021, Quansight"
author = "Quansight"

# The short X.Y version
# version = re.match(r"^([0-9]+\.[0-9]+).*", release).group(1)


# -- General configuration ---------------------------------------------------

BLOG_TITLE = title = html_title = "Docs"
BLOG_AUTHOR = author = "Quansight"
html_theme = "sphinx_material"

# The master toctree document.
master_doc = "index"

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
source_suffix = ".md .rst .ipynb .py".split()

extensions = [
    "myst_parser",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    ]

# autoapi.extension
exclude_patterns = ("_build", "*checkpoint*", "output", "outputs", "README.md")
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

# Material theme options (see theme.conf for more information)

html_theme_options = {
    "nav_title": "Welcome to QHub's documentation!",
    # 'google_analytics_account': 'UA-XXXXX',     
    # Set you GA account ID to enable tracking
    # Specify a base_url used to generate sitemap.xml. If not, no sitemap will be built.
    "base_url": "https://qhub.dev/",
    # Set the color and the accent color
    "theme_color": THEME_COLOR,
    "color_primary": THEME_COLOR,
    "color_accent": "light-yellow",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/Quansight/qhub",
    "repo_name": "QHub",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 2,
    # If False, expand all TOC entries
    "globaltoc_collapse": True,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": False,

    "nav_links": [
            {
            "href": "https://www.quansight.com/jupyter-consulting",
            "title": "Quansight",
            "internal": False,

        },
            {
            "href": "https://hpc.qhub.dev/",
            "title": "QHub HPC",
            "internal": False,

        },
            {
                "href": "https://pypi.org/project/qhub/",
                "title": "PyPI",
                "internal": False,

        },
        ],

    }

html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
    }

# Exclude build directory and Jupyter backup files:
exclude_patterns = ["_build", "*checkpoint*", "site", "jupyter_execute", "conf.py", "README.md"]

latex_documents = [
    (master_doc, "qhub.tex", "Infrastructure as Code", "QHub", "manual",)
    ]

jupyter_execute_notebooks = "off"

myst_update_mathjax = False

# SITE_URL = "https://quansight.github.io/qhub-home/"
