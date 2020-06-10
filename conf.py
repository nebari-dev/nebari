# import sphinx.writers.html5
# sphinx.writers.html5.HTML5Translator.visit_pending_xref = lambda *x:...
# sphinx.writers.html5.HTML5Translator.depart_pending_xref = lambda *x:...
BLOG_TITLE = title = html_title = "Qhub code as infrastructure."
BLOG_AUTHOR = author = "Quansight"
html_theme = "pydata_sphinx_theme"
master_doc = "README"
source_suffix = ".rst .md .ipynb .py".split()
#extensions = "recommonmark nbsphinx sphinx.ext.autodoc sphinx.ext.coverage sphinx.ext.napoleon autoapi.extension sphinx.ext.mathjax sphinx_copybutton     sphinx.ext.viewcode".split()
extensions = "recommonmark nbsphinx".split()

html_theme = 'sphinx_material'

# Material theme options (see theme.conf for more information)
html_theme_options = {

    # Set the name of the project to appear in the navigation.
    'nav_title': 'Project Name',

    # Set you GA account ID to enable tracking
    #'google_analytics_account': 'UA-XXXXX',

    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    'base_url': 'https://project.github.io/project',

    # Set the color and the accent color
    'color_primary': 'blue',
    'color_accent': 'light-blue',

    # Set the repo location to get a badge with stats
    'repo_url': 'https://github.com/project/project/',
    'repo_name': 'Project',

    # Visible levels of the global TOC; -1 means unlimited
    'globaltoc_depth': 3,
    # If False, expand all TOC entries
    'globaltoc_collapse': False,
    # If True, show hidden TOC entries
    'globaltoc_includehidden': False,
}

# Exclude build directory and Jupyter backup files:
exclude_patterns = ["_build", "*checkpoint*"]
autoapi_type = "python"
autoapi_dirs = []


nbsphinx_prolog = """.. raw:: html
    
    <style>.prompt {
        display: none;
    }</style>
"""

latex_documents = [
    (master_doc, "pidgy.tex", "Infrastructure as Code", "QHub", "manual",)
]
