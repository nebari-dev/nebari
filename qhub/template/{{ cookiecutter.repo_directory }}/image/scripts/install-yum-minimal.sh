yum -y update && \
    yum install -y wget bzip2 ca-certificates curl git && \
    yum clean all && \
    rm -rf /var/cache/yum
