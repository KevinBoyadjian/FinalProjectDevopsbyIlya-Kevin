# 1. Create the WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.project_name}-web-acl"
  description = "WAF for CloudFront with Managed Rule Sets"
  scope       = "CLOUDFRONT" # Must be CLOUDFRONT for use with a Distribution

  default_action {
    allow {}
  }

  # Rule: AWS Managed Common Rule Set (Protects against OWASP Top 10)
  rule {
    name     = "AWS-AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-waf-metric"
    sampled_requests_enabled   = true
  }

  tags = var.common_tags
}


# 2. CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.project_name} Flask App"
  default_root_object = ""

  aliases = ["top5score.com", "www.top5score.com"]

  # Link the WAF we just created
  web_acl_id = aws_wafv2_web_acl.main.arn

  # The 'Origin' is your ALB. 
  # Note: Since the ALB is created by the K8s Ingress Controller.
  # This ensures CloudFront always looks at the same place, and the ExternalDNS controller ensures that place always points to the right ALB.

  origin {
    domain_name = "origin.top5score.com"
    origin_id   = "ALB-Origin"

# THE SECRET HANDSHAKE
    custom_header {
      name  = "X-Custom-Header"
      value = var.alb_handshake_secret
    }

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only" # EKS ALB usually receives HTTP from CF
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    # The Required Arguments
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-Origin"
    
    # Force users to use https
    viewer_protocol_policy = "redirect-to-https" # Force HTTPS for users


    # The Live Score Behavior Settings (cache)
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none" # Allow access from all countries
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.common_tags
}
