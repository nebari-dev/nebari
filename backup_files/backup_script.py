#!/usr/bin/python
from datetime import datetime
import os
from fsspec import get_fs_token_paths
import sys
import json

t = datetime.utcnow()

try:
    backup_bucket = sys.argv[1]  # Grabs bucket name command line argument
except:
    print("Missing command line arguments for bucket name. Backup not performed")
    sys.exit(1)

try:
    cloud_provider = sys.argv[2]  # Sets the cloud provider type [aws, gcp, do]
except:
    print("Missing command line arguments for cloud provider. Backup not performed")
    sys.exit(1)

f_name = f"{t.strftime('%Y-%m-%d_%H-%M-%S')}_UTC_shared_nfs_backup.tar.gz"

# Creates fsspec filesystem based on the envrinment variables of the indicated cloud provider
if cloud_provider == "aws":
    key = os.environ["AWS_ACCESS_KEY_ID"]
    secret = os.environ["AWS_SECRET_ACCESS_KEY"]
    creds = {"key": key, "secret": secret}
    fs, _, _ = get_fs_token_paths(backup_bucket, storage_options=creds)

if cloud_provider == "gcp":
    creds = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    fs, _, _ = get_fs_token_paths(
        backup_bucket, storage_options={"token": json.loads(creds)}
    )

os.system(
    f"tar -zcvf {f_name} ./shared_nfs/"
)  # Tarballs the shared_nfs folder. This will keep permissions and groups

fs.put(f_name, f"{backup_bucket}/{f_name}")  # Uploads backup file to cloud storage
