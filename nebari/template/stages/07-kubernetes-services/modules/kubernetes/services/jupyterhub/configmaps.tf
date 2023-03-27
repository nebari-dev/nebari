locals {
  jupyter_notebook_config_py_template = templatefile("${path.module}/files/jupyter/jupyter_notebook_config.py.tpl", {
    terminal_cull_inactive_timeout      = var.terminal_cull_inactive_timeout
    terminal_cull_interval              = var.terminal_cull_interval
    kernel_cull_idle_timeout            = var.kernel_cull_idle_timeout
    kernel_cull_interval                = var.kernel_cull_interval
    kernel_cull_connected               = var.kernel_cull_connected ? "True" : "False" # for Python compatible boolean values
    kernel_cull_busy                    = var.kernel_cull_busy ? "True" : "False"      # for Python compatible boolean values
    server_shutdown_no_activity_timeout = var.server_shutdown_no_activity_timeout
    }
  )
}


resource "local_file" "jupyter_notebook_config_py" {
  content  = local.jupyter_notebook_config_py_template
  filename = "${path.module}/files/jupyter/jupyter_notebook_config.py"
}


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
  depends_on = [
    local_file.jupyter_notebook_config_py
  ]

  metadata {
    name      = "etc-jupyter"
    namespace = var.namespace
  }

  data = {
    "jupyter_notebook_config.py" : local_file.jupyter_notebook_config_py.content
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
