# Using Curl to access AWS S3

In some situations, users may wish to upload content to S3 or download content from an S3 bucket. For example, when attempting [manual backups of QHub's data](./backup.md).

In many cases, the most straightforward way to access AWS S3 buckets is by installing and using AWS's command-line tool. But in some situations - for example, to back up the
JupyterHub SQLite database - it may be difficult to install AWS' CLI tools due to being in a restricted container environment. In that situation, it is possible to fall back on
AWS' basic REST API and use HTTPS requests directly instead. (Ultimately, the AWS CLI is simply a wrapper around those REST APIs.)

This document describes how to use `curl` commands to interface with S3 directly, specifically in the case of [uploading a backup of JupyterHub's SQLite database](./backup.md) from
a restricted pod to S3 (or restoring it from a backup from S3).

## Common settings

These settings will be needed whether uploading or downloading:

```bash
s3_access_key=<AWS Key>
s3_secret_key=<AWS Secret>
region=us-west-2
bucket=<AWS bucket name>
```

## Upload to s3

```bash
# File locations
file_to_upload=/srv/jupyterhub/jupyterhub.sqlite
output_filename=backups/jupyterhub.sqlite

# Metadata
filepath="/${bucket}/${output_filename}"
contentType="application/x-compressed-tar"
dateValue=`date -R`
signature_string="PUT\n\n${contentType}\n${dateValue}\n${filepath}"

#prepare signature hash to be sent in Authorization header
signature_hash=`echo -en ${signature_string} | openssl sha1 -hmac ${s3_secret_key} -binary | base64`

# Send file to S3 using Curl
curl -X PUT -T "${file_to_upload}" \
  -H "Host: ${bucket}.s3.amazonaws.com" \
  -H "Date: ${dateValue}" \
  -H "Content-Type: ${contentType}" \
  -H "Authorization: AWS ${s3_access_key}:${signature_hash}" \
  https://${bucket}.s3-${region}.amazonaws.com/${output_filename}
```

## Download from S3

```bash
output_file=/srv/jupyterhub/jupyterhub.sqlite
s3_file=backups/jupyterhub.sqlite

# Metadata
resource="/${bucket}/${s3_file}"
contentType="binary/octet-stream"
dateValue=`TZ=GMT date -R`
# You can leave out "TZ=GMT" if your system is already GMT (but don't have to)

stringToSign="GET\n\n${contentType}\n${dateValue}\n${resource}"

signature=`echo -en ${stringToSign} | openssl sha1 -hmac ${s3_secret_key} -binary | base64`

# Fetch file from S3 using curl
curl -H "Host: s3-${region}.amazonaws.com" \
     -H "Date: ${dateValue}" \
     -H "Content-Type: ${contentType}" \
     -H "Authorization: AWS ${s3_access_key}:${signature}" \
     https://s3-${region}.amazonaws.com/${bucket}/${s3_file} -o $output_file
```

______________________________________________________________________

Inspired by [this article on how to use curl to upload files to was s3](https://www.gyanblog.com/aws/how-upload-aws-s3-curl/) and
[this StackOverflow answer on how to access was s3 buckets](https://stackoverflow.com/a/57516606/2792760).
