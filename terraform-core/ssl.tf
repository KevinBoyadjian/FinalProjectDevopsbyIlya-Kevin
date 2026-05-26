# 1. Request the SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = "top5score.com"
  subject_alternative_names = ["*.top5score.com"] # Protects subdomains like grafana. and api.
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = var.common_tags
}

# 2. Automatically create the DNS record to "Prove" you own the domain
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = "Z009328231GYPRN2AA3CY" # Your Hosted Zone ID
}

# 3. This tells Terraform to WAIT until the certificate is active
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

