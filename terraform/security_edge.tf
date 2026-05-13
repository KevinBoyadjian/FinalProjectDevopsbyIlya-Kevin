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

  # Link the WAF we just created
  web_acl_id = aws_wafv2_web_acl.main.arn

  # The 'Origin' is your ALB. 
  # Note: Since the ALB is created by the K8s Ingress Controller, 
  # we usually have to find its DNS name manually or via a Data Source 
  # AFTER the first deployment. For now, we use a descriptive placeholder.
  origin {
    domain_name = "example.com" # Temporary name 
    origin_id   = "ALB-Origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only" # EKS ALB usually receives HTTP from CF
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-Origin"

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https" # Force HTTPS for users
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none" # Allow access from all countries
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true # Use *.cloudfront.net certificate for now
  }

  tags = var.common_tags
}


