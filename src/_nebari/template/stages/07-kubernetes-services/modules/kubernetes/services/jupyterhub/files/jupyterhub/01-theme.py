from nebari_jupyterhub_theme import theme_extra_handlers, theme_template_paths

c.JupyterHub.extra_handlers.extend(theme_extra_handlers)
c.JupyterHub.template_paths.extend(theme_template_paths)

import z2jh  # noqa: E402

jupyterhub_theme = z2jh.get_config("custom.theme")

c.JupyterHub.template_vars = {
    **jupyterhub_theme,
}
