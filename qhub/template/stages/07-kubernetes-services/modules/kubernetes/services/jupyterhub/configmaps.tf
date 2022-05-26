resource "kubernetes_config_map" "etc-ipython" {
  metadata {
    name      = "etc-ipython"
    namespace = var.namespace
  }

  data = {
    for filename in fileset("${path.module}/files/ipython", "*") :
    filename => file("${path.module}/files/ipython/${filename}")
  }
}


resource "kubernetes_config_map" "etc-jupyter" {
  metadata {
    name      = "etc-jupyter"
    namespace = var.namespace
  }

  data = {
    for filename in fileset("${path.module}/files/jupyter", "*") :
    filename => file("${path.module}/files/jupyter/${filename}")
  }
}


resource "kubernetes_config_map" "etc-skel" {
  metadata {
    name      = "etc-skel"
    namespace = var.namespace
  }

  data = {
    for filename in fileset("${path.module}/files/skel", "*") :
    filename => file("${path.module}/files/skel/${filename}")
  }
}


resource "kubernetes_config_map" "jupyterlab-settings" {
  metadata {
    name      = "jupyterlab-settings"
    namespace = var.namespace
  }

  data = {
    for filename in fileset("${path.module}/files/jupyterlab", "*") :
    filename => file("${path.module}/files/jupyterlab/${filename}")
  }
}


resource "kubernetes_config_map" "shared-examples" {
  metadata {
    name      = "shared-examples"
    namespace = var.namespace
  }

  data = {
    for filename in fileset("${path.module}/files/examples", "*") :
    filename => file("${path.module}/files/examples/${filename}")
  }
}
