output "cluster_name" {
    description = "The name of the EKS cluster"
    value       = module.eks_cluster.cluster_name
}

output "cluster_endpoint" {
    description = "The endpoint for the EKS cluster"
    value       = module.eks_cluster.cluster_endpoint
}

output "cluster_certificate_authority_data" {
    description = "The base64 encoded certificate authority data for the EKS cluster"
    value       = module.eks_cluster.cluster_certificate_authority_data
}

output "vpc_id" {
    description = "The ID of the VPC"
    value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
    description = "List of IDs of private subnets"
    value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
    description = "List of IDs of public subnets"
    value       = module.vpc.public_subnets
}

output "kubeconfig_command" {
    description = "Command to update your local kubeconfig"
    value       = "aws eks update-kubeconfig --region ${var.aws_region} -- name ${module.eks_cluster.cluster_name}"
}

# 1. The CloudFront URL
# This is the public address of your global website
output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

# 2. The WAF Web ACL ARN
# Useful if you need to troubleshoot or link it to other resources later
output "waf_web_acl_arn" {
  description = "The ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.arn
}

# 3. The IAM Role ARN for the Load Balancer Controller
# Helpful to verify the IRSA connection
output "lb_controller_role_arn" {
  description = "The ARN of the IAM role for the AWS Load Balancer Controller"
  value       = aws_iam_role.lb_controller.arn
}

# 4. Reminder command for kubeconfig
# This is a "UX" output that gives you the exact command to run
output "update_kubeconfig_command" {
  description = "Command to update your local kubeconfig to connect to the cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks_cluster.cluster_name}"
}

