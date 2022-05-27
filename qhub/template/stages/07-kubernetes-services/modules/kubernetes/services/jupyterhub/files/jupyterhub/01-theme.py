from qhub_jupyterhub_theme import theme_extra_handlers, theme_template_paths

c.JupyterHub.extra_handlers.extend(theme_extra_handlers)
c.JupyterHub.template_paths.extend(theme_template_paths)

import z2jh  # noqa: E402

jupyterhub_theme = z2jh.get_config("custom.theme")
cdsdashboards = z2jh.get_config("custom.cdsdashboards")

c.JupyterHub.template_vars = {
    **jupyterhub_theme,
    "cdsdashboards_enabled": cdsdashboards["enabled"],
    "cds_hide_user_named_servers": cdsdashboards["cds_hide_user_named_servers"],
    "cds_hide_user_dashboard_servers": cdsdashboards["cds_hide_user_dashboard_servers"],
}
