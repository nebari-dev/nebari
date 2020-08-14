# Theming

## JupyterHub Theme

The QHub theme was originally based off the [work of the pangeo
team](https://github.com/pangeo-data/pangeo-custom-jupyterhub-templates)
and is now located in
[github.com/Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme/). For
simple modifications to the jupyterhub theme we suggest only editing
`infrastructure/jupyterhub.yaml` and the value
`c.JupyterHub.template_vars`. For most use cases this should provide
enough flexibility.

```yaml
hub:
  extraConfig:
    customPodHook: |
      c.JupyterHub.template_paths = ['/usr/local/share/jupyterhub/custom_templates/']
      c.JupyterHub.template_vars = {
          'pangeo_hub_title': 'QHub - $do-jupyterhub',
          'pangeo_hub_subtitle': 'Autoscaling Compute Environment on Digital Ocean',
          'pangeo_welcome': """Welcome to $. It is maintained by the <a href="http://quansight.com">Quansight staff</a>. The hub's configuration is stored in the github repository based on <a href="https://github.com/Quansight/qhub-kubernetes/">https://github.com/Quansight/qhub-kubernetes/</a>. To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub-kubernetes//issues">github issue tracker</a>."""
      }
```

For more serious modifications to the jupyterhub theme you will need
to fork
[Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme)
and edit the jupyterhub Dockerfile located at
`image/Dockerfile.jupyterhub`. Modify the `THEME_OWNER`, `THEME_REPO`,
and `THEME_REV`. This should change the Dockerfile to use your new
theme. The
[Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme)
has detailed documentation.

## Jupyterlab Theme

Setting the JupyterLab theme is done via extensions. Edit the
`image/postBuild` script to include the jupyterlab extension in the
build. Within the `image` directory run the following to build
jupyterlab.

```shell
docker build -f Docker.jupyterlab -t Quansight/qhub-jupyterlab:latest .
```

Finally you can test the resulting image via the following docker
command and open your web browser to `localhost:8000`.

```shell
docker run -p 8000:8000 -it Quansight/qhub-jupyterlab:latest jupyter lab --port 8000 --ip 0.0.0.0
```
