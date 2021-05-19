"""
This is a hard replace as soon as the source file is read, so no respect for any markup at all
Simply forces replace of ||QHUB_VERSION|| with the qhub_version_string in conf.py
"""

def dosubs(app, docname, source):
    """
    Replace QHUB_VERSION with the qhub version
    """
    if app.config.qhub_version_string != '':
        src = source[0]
        source[0] = src.replace('||QHUB_VERSION||', app.config.qhub_version_string)

def setup(app):
    app.connect("source-read", dosubs)
    app.add_config_value('qhub_version_string', '', 'env')
