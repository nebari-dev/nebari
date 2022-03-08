from nox import session


@session(reuse_venv=True)
def docs(session):
    session.install("-e.")
    session.install("-rdocs/requirements.txt")
    session.run("sphinx-build", "docs", "_build/html")
