# To help jupyterhub-idle-culler cull user servers, we configure the kernel manager to cull
# idle kernels that would otherwise make the user servers report themselves as active which
# is part of what jupyterhub-idle-culler considers.

# Extra config available at:
# https://zero-to-jupyterhub.readthedocs.io/en/1.x/jupyterhub/customizing/user-management.html#culling-user-pods

# Shut down the server after N seconds with no kernels or terminals running and no activity.
# c.NotebookApp.shutdown_no_activity_timeout = 400

c.TerminalManager.cull_inactive_timeout = 120
c.TerminalManager.cull_interval = 60

# cull_idle_timeout: timeout (in seconds) after which an idle kernel is
# considered ready to be culled
c.MappingKernelManager.cull_idle_timeout = 3 * 60

# cull_interval: the interval (in seconds) on which to check for idle
# kernels exceeding the cull timeout value
c.MappingKernelManager.cull_interval = 90

# cull_connected: whether to consider culling kernels which have one
# or more connections
c.MappingKernelManager.cull_connected = True

# cull_busy: whether to consider culling kernels which are currently
# busy running some code
c.MappingKernelManager.cull_busy = False