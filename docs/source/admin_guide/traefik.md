# Traefik

## Custom TLS certificate

### Creating the certificate

[Lego](https://go-acme.github.io/lego/installation/) is a command line tool for provisioning certificates for a domain. If you are trying to install QHub within an enterprise you
may need to contact someone in IT to create the certificate and key-pair for you. Ensure that this certificate has all of the domains that QHub is running on. Lego supports
[multiple DNS providers](https://go-acme.github.io/lego/dns/). For this example we will assume Cloudflare as your DNS provider.

```shell
export CLOUDFLARE_DNS_API_TOKEN=1234567890abcdefghijklmnopqrstuvwxyz
lego --email myemail@example.com --dns cloudflare --domains my.example.org run
```

Or alternatively for testing you can create a self-signed certificate. This should only be used for testing.

```shell
export QHUB_DOMAIN=github-actions.qhub.dev
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 \
  -subj "/C=US/ST=Oregon/L=Portland/O=Quansight/OU=Org/CN=$QHUB_DOMAIN" \
  -nodes
```

### Adding certificate to kubernetes cluster as a secret

You can name the certificate anything you would like `qhub-domain-certificate` is only an example.

```
kubectl create secret tls qhub-domain-certificate -n dev \
  --cert=cert.pem \
  --key=key.pem
```

### Using custom certificate in qhub-config.yaml

Once you have followed these steps make sure to modify the configuration to use the new certificate.

```
certificate:
  type: existing
  secret_name: qhub-domain-certificate
```
