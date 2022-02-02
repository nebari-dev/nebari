# Should consider
# https://github.com/CentOS/sig-cloud-instance-images/issues/190
find /etc/yum.repos.d/ -type f -exec sed -i 's/mirrorlist=/#mirrorlist=/g' {} +
find /etc/yum.repos.d/ -type f -exec sed -i 's/#baseurl=/baseurl=/g' {} +
find /etc/yum.repos.d/ -type f -exec sed -i 's/mirror.centos.org/vault.centos.org/g' {} +

yum -y update && \
    yum install -y wget bzip2 ca-certificates curl git && \
    yum clean all && \
    rm -rf /var/cache/yum /var/tmp/* /tmp/*
