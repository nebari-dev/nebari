# Using Curl to access AWS S3

How to upload/download to S3 using only curl (for example, when uploading a [backup](./backup.md) from a restricted pod).

Inspired by [this article](So we just need to upload the file to S3. You might want to install the AWS CLI tool as we did before, but unfortunately the Hub container is quite locked down and it isn't straightforward to install that... You might need to upload to S3 using curl directly:

## Common settings

These settings will be needed whether uploading or downloading:

```
s3_access_key=<AWS Key>
s3_secret_key=<AWS Secret>
region=us-west-2
bucket=<AWS bucket name>
```

## Upload to s3

```
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

```
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


---
Inspired by [this article](https://www.gyanblog.com/aws/how-upload-aws-s3-curl/) and [this one](https://stackoverflow.com/a/57516606/2792760).
