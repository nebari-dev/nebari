"""
This is a hard replace as soon as the source file is read, so no respect for any markup at all
Simply forces replace of ||nebari_VERSION|| with the nebari_version_string in conf.py
"""


def dosubs(app, docname, source):
    """
    Replace nebari_VERSION with the nebari version
    """
    if app.config.nebari_version_string != "":
        src = source[0]
        source[0] = src.replace("||nebari_VERSION||", app.config.nebari_version_string)


def setup(app):
    app.connect("source-read", dosubs)
    app.add_config_value("nebari_version_string", "", "env")
