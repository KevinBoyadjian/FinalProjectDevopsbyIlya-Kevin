variable "aws_region" {
    description = "AWS region for deploying infrastructure"
    type        = string
    default     = "us-east-1"
}

variable "project_name" {
    description = "Unique name for the project to prefix resources"
    type        = string
    default     = "flask-devsecops"
}

variable "environment" {
    description = "Deployment environment (e.g., dev, staging, prod)"
    type        = string
    default     = "dev" # Default to 'dev' for initial setup
}

variable "cluster_version" {
    description = "kubernetes version for the EKS cluster"
    type        = string
    default     = "1.30"
}

variable "instance_types" {
    description = "List of instance types for EKS worker nodes"
    type        = list(string)
    default     = ["t3.medium"]
}

variable "desired_node_size" {
    description = "Desired number of worker nodes"
    type        = number
    default     = 2
}

variable "min_node_size" {
    description = "Minimum number of worker nodes"
    type        = number
    default     = 1
}

variable "max_node_size" {
    description = "Maximum number of worker nodes"
    type        = number
    default     = 3
}

variable "vpc_cidr" {
    description = "CIDR block for the VPC"
    type        = string
    default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
    description = "CIDR blocks for public subnets"
    type        = list(string)
    default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
    description = "CIDR blocks for private subnets"
    type        = list(string)
    default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "common_tags" {
    description = "Common tags for all resources"
    type        = map(string)
    default     = {
        ManagedBy = "Terraform"
        project   = "DevSecOpsFlask"
    }
variable "alb_handshake_secret" {
    description = "The secret header value for CloudFront to ALB authentication"
    type        = string
    sensitive   = true # This masks the password in the logs
    }
}