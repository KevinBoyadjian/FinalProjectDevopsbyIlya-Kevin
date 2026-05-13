# EKS Cluster (using the official module)
module "eks_cluster" {
    source  = "terraform-aws-modules/eks/aws"
    version = "~> 19.0" # Use a compatible version

    cluster_name    = "${var.project_name}-${var.environment}-eks"
    cluster_version = var.cluster_version
    vpc_id          = module.vpc.vpc_id
    subnet_ids      = module.vpc.private_subnets # EKS control plane uses private subnets

    # EKS Managed Node Group
    eks_managed_node_groups = {
        default = {
            instance_types = var.instance_types
            desired_size   = var.desired_node_size
            min_size       = var.min_node_size
            max_size       = var.max_node_size

            #Additional settings for the node group ( e.g., disk size, labels)
            disk_size = 20
            tags = {
                Name = "${var.project_name}-node"
            }
        }
    }

    # Cluster endpoint access
    cluster_endpoint_private_access = true
    cluster_endpoint_public_access  = true
    # Add specific CIDR blocks if you want to restrict public access to control plane
    # cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

    tags = var.common_tags
}
