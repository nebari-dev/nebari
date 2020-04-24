# Themeing

## JupyterHub Theme

The QHub theme was originally based off the [work of the pangeo
team](https://github.com/pangeo-data/pangeo-custom-jupyterhub-templates)
and is now located in
[github.com/Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme/). The
simplest solution would be to Fork the github repo and customize the
theme to your needs. In addition to creating a new repo for the github
theme you will need to modify the `infrastructure/jupyterhub.yaml`
script. Setting `c.JupyterHub.template_vars` allows you to customize
the variables within your jinja template theme. Additionally you will
need to change the `repository` and `revision`.

```yaml
hub:
  extraConfig:
    01-jupyterlab: |
      c.Spawner.cmd = ['jupyter-labhub']

    customPodHook: |
      c.JupyterHub.template_paths = ['/usr/local/share/jupyterhub/custom_templates/']
      c.JupyterHub.template_vars = {
          'pangeo_hub_title': 'QHub - ${{ cookiecutter.project_name }}',
          'pangeo_hub_subtitle': 'Autoscaling Compute Environment on Digital Ocean',
          'pangeo_welcome': """Welcome to ${{ cookiecutter.endpoint }}. It is maintained by the <a href="http://quansight.com">Quansight staff</a>. The hub's configuration is stored in the github repository based on <a href="https://github.com/Quansight/qhub-kubernetes/">https://github.com/Quansight/qhub-kubernetes/</a>. To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub-kubernetes//issues">github issue tracker</a>."""
      }
  extraVolumes:
    - name: custom-templates
      gitRepo:
        repository: "https://github.com/Quansight/qhub-jupyterhub-theme.git"
        revision: "53edc55d0bdd5944fb6dee2d10af90da8faf191d"
  extraVolumeMounts:
    - mountPath: /usr/local/share/jupyterhub/custom_templates
      name: custom-templates
      subPath: "qhub-jupyterhub-theme/templates"
    - mountPath: /usr/local/share/jupyterhub/static/extra-assets
      name: custom-templates
      subPath: "qhub-jupyterhub-theme/extra-assets"
```

> TODO: should we bake the theme into a custom jupyterhub docker image?
> This would be easy and would be similar to the approach we take with
> themeing jupyterlab. Not to mention testing would be easier.

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
