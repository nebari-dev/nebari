#!/usr/bin/python
from datetime import datetime
import os
from fsspec import get_fs_token_paths
import sys

t = datetime.utcnow()

f_name = f"{t.strftime('%Y-%m-%d_%H-%M-%S')}_UTC_shared_nfs_backup.tar.gz"

os.system(
    f"tar -zcvf {f_name} ./shared_nfs/"
)  # Tarballs the shared_nfs folder. This will keep permissions and groups

backup_bucket = sys.argv[1]  # Grabs bucket name command line argument
fs, _, _ = get_fs_token_paths(
    backup_bucket, storage_options={"token": "cloud"}
)  # creates an fs bucket
fs.put(f_name, f"{backup_bucket}/{f_name}")