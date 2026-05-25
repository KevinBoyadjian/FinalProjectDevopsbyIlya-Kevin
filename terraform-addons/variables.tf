variable "grafana_admin_password" {
  description = "The admin password for Grafana"
  type        = string
  sensitive   = true
}

variable "aws_region" {
  description = "AWS region for resources"
  type	      = string
  default     = "us-east-1"
}

variable "alb_handshake_secret" {
  description = "The secret header value for CloudFront to ALB authentication"
  type        = string
  sensitive   = true # This masks the password in the logs
}
