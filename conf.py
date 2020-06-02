# import sphinx.writers.html5
# sphinx.writers.html5.HTML5Translator.visit_pending_xref = lambda *x:...
# sphinx.writers.html5.HTML5Translator.depart_pending_xref = lambda *x:...
BLOG_TITLE = title = html_title = "Qhub code as infrastructure."
BLOG_AUTHOR = author = "Quansight"
html_theme = "pydata_sphinx_theme"
master_doc = "README"
source_suffix = ".rst .md .ipynb .py".split()
#extensions = "recommonmark nbsphinx sphinx.ext.autodoc sphinx.ext.coverage sphinx.ext.napoleon autoapi.extension sphinx.ext.mathjax sphinx_copybutton     sphinx.ext.viewcode".split()
extensions = "nbsphinx".split()

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
