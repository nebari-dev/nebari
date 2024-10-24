# To help jupyterhub-idle-culler cull user servers, we configure the kernel manager to cull
# idle kernels that would otherwise make the user servers report themselves as active which
# is part of what jupyterhub-idle-culler considers.

# Extra config available at:
# https://zero-to-jupyterhub.readthedocs.io/en/1.x/jupyterhub/customizing/user-management.html#culling-user-pods

# Refuse to serve content from handlers missing authentication guards, unless
# the handler is explicitly allow-listed with `@allow_unauthenticated`; this
# prevents accidental exposure of information by extensions installed in the
# single-user server when their handlers are missing authentication guards.
c.ServerApp.allow_unauthenticated_access = False

# Enable Show Hidden Files menu option in View menu
c.ContentsManager.allow_hidden = True
c.FileContentsManager.allow_hidden = True

# Set the preferred path for the frontend to start in
c.FileContentsManager.preferred_dir = "${jupyterlab_preferred_dir}"

# Timeout (in seconds) in which a terminal has been inactive and ready to
# be culled.
c.TerminalManager.cull_inactive_timeout = ${terminal_cull_inactive_timeout} * 60

# The interval (in seconds) on which to check for terminals exceeding the
# inactive timeout value.
c.TerminalManager.cull_interval = ${terminal_cull_interval} * 60

# cull_idle_timeout: timeout (in seconds) after which an idle kernel is
# considered ready to be culled
c.MappingKernelManager.cull_idle_timeout = ${kernel_cull_idle_timeout} * 60

# cull_interval: the interval (in seconds) on which to check for idle
# kernels exceeding the cull timeout value
c.MappingKernelManager.cull_interval = ${kernel_cull_interval} * 60

# cull_connected: whether to consider culling kernels which have one
# or more connections
c.MappingKernelManager.cull_connected = ${kernel_cull_connected}

# cull_busy: whether to consider culling kernels which are currently
# busy running some code
c.MappingKernelManager.cull_busy = ${kernel_cull_busy}

# Shut down the server after N seconds with no kernels or terminals
# running and no activity.
c.NotebookApp.shutdown_no_activity_timeout = ${server_shutdown_no_activity_timeout} * 60

###############################################################################
# JupyterHub idle culler total timeout corresponds (approximately) to:
# max(cull_idle_timeout, cull_inactive_timeout) + shutdown_no_activity_timeout

from argo_jupyter_scheduler.executor import ArgoExecutor
from argo_jupyter_scheduler.scheduler import ArgoScheduler

c.Scheduler.execution_manager_class=ArgoExecutor
c.SchedulerApp.scheduler_class=ArgoScheduler
c.SchedulerApp.scheduler_class.use_conda_store_env=True
