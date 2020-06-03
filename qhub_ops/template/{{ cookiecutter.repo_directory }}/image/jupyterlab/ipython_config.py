# Disable history manager, we don't really use it
# and by default it puts an sqlite file on NFS, which is not something we wanna do
c.Historymanager.enabled = False
