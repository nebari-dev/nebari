# Culling idle notebook servers

Qhub uses a mix of the `idle culler <https://github.com/jupyterhub/jupyterhub-idle-culler>`\_ extension and internal
Jupyterlab server configuration to periodically check for idle notebook servers and shut them down.

JupyterHub pings the user's notebook server at certain time intervals. If no response is received from the server during
this checks and the timeout expires, the server is considered to be *inactive (idle)* and will be culled.

To help jupyterhub-idle-culler cull user servers, we configure the kernel manager to cull idle kernels that would
otherwise make the user servers report themselves as active which is part of what jupyterhub-idle-culler considers.

______________________________________________________________________

The expected behavior is that the server will be shut down and removed from the Qhub namespace once all Terminals and
Kernels are considered idle or terminated, as well as any remaining connection is closed.

______________________________________________________________________

## Default settings

By default, JupyterHub will ping the user notebook servers every 5 minutes to check their status. Every server found to
be idle for more than 30 minutes will be terminated.

Because the servers don't have a maximum age set, an active (has any open connection, terminal or kernel in execution )
server will not be shut down regardless of how long it has been up and running.

The process for culling and terminating follows these steps:

- Check if the Terminal and Notebooks kernels are idle for more than 15 minutes. With periodically culling checks of 5m.
- If the kernel is idle for more than 15 minutes, terminate the kernel and the server.
- Once no connections remains, after another 15m of no API calls from the user pod, the server is considered idle, and
  will be terminated.
