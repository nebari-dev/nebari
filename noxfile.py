from nox import session

@session(reuse_venv=True)
def docs(session):
    session.install("-e.")
    session.install("jupyter-book")
    session.run("sphinx-build", "-c", "docs",".", "_build/html")