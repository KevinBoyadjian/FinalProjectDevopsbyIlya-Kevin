variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "grafana_admin_password" {
  description = "The admin password for Grafana"
  type        = string
  sensitive   = true
}

