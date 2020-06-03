# Authentication

Authentication into the jupyterhub cluster can be done several
ways. This guide for now will focus on the GitHub authentication.

## Github OAuth

The authentication component of the cluster can be found in
[infrastruture/jupyterhub.yaml](../infrastruture/jupyterhub.yaml). In
order to use GitHhub OAuth an OAuth app must be create by a
user. *TODO:* Directions can be found <here>.

```yaml
auth:
  type: github
  github:
    clientId: "<client-id>"
    clientSecret: "<client-secret>"
    callbackUrl: "https://<url>/hub/oauth_callback"
  admin:
    access: true
    users:
      - <github-username1>
      ...
  whitelist:
    users:
      - <github-username2>
      ...
```
