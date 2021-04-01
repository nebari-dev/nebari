import os


# Disable history manager, we don't really use it and by default it
# puts an sqlite file on NFS, which is not something we wanna do
c.Historymanager.enabled = False


# Change default umask for all subprocesses of the notebook server if
# set in the environment
if "NB_UMASK" in os.environ:
    os.umask(int(os.environ["NB_UMASK"], 8))
