resource "kubernetes_config_map" "etc-ipython" {
  metadata {
    name      = "etc-ipython"
    namespace = var.namespace
  }

  data = {
    "ipython_config.py"          = file("${path.module}/files/ipython/ipython_config.py")
  }
}


resource "kubernetes_config_map" "etc-jupyter" {
  metadata {
    name      = "etc-jupyter"
    namespace = var.namespace
  }

  data = {
    "jupyter_notebook_config.py" = file("${path.module}/files/jupyter/jupyter_notebook_config.py")
  }
}


resource "kubernetes_config_map" "etc-skel" {
  metadata {
    name      = "etc-skel"
    namespace = var.namespace
  }

  data = {
    ".profile"     = file("${path.module}/files/skel/.profile")
    ".bashrc"      = file("${path.module}/files/skel/.bashrc")
    ".bash_logout" = file("${path.module}/files/skel/.bash_logout")
  }
}


resource "kubernetes_config_map" "jupyterlab-settings" {
  metadata {
    name      = "jupyterlab-settings"
    namespace = var.namespace
  }

  data = {
    "overrides.json" = file("${path.module}/files/jupyterlab/overrides.json")
  }
}
