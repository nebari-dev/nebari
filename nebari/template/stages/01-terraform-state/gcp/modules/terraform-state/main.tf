module "gcs" {
  source = "../gcs"

  name          = "${var.name}-terraform-state"
  location      = var.location
  public        = false
  force_destroy = true

}
