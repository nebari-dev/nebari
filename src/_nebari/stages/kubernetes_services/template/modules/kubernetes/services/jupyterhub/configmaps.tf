locals {
  jupyter-notebook-config-py-template = templatefile("${path.module}/files/jupyter/jupyter_server_config.py.tpl", {
    terminal_cull_inactive_timeout      = var.idle-culler-settings.terminal_cull_inactive_timeout
    terminal_cull_interval              = var.idle-culler-settings.terminal_cull_interval
    kernel_cull_idle_timeout            = var.idle-culler-settings.kernel_cull_idle_timeout
    kernel_cull_interval                = var.idle-culler-settings.kernel_cull_interval
    kernel_cull_connected               = var.idle-culler-settings.kernel_cull_connected ? "True" : "False" # for Python compatible boolean values
    kernel_cull_busy                    = var.idle-culler-settings.kernel_cull_busy ? "True" : "False"      # for Python compatible boolean values
    server_shutdown_no_activity_timeout = var.idle-culler-settings.server_shutdown_no_activity_timeout
    }
  )
}


resource "local_file" "jupyter_server_config_py" {
  content  = local.jupyter-notebook-config-py-template
  filename = "${path.module}/files/jupyter/jupyter_server_config.py"
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
    local_file.jupyter_server_config_py
  ]

  metadata {
    name      = "etc-jupyter"
    namespace = var.namespace
  }

  data = {
    "jupyter_server_config.py" : local_file.jupyter_server_config_py.content
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
