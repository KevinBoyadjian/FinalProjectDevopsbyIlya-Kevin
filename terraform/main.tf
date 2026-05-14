# EKS Cluster (using the official module)
module "eks_cluster" {
    source  = "terraform-aws-modules/eks/aws"
    version = "~> 20.0" # Use a compatible version
    kms_key_administrators = ["arn:aws:iam::219127327432:user/ilya"]
    
    cluster_name    = "${var.project_name}-${var.environment}-eks"
    cluster_version = var.cluster_version
    vpc_id          = module.vpc.vpc_id
    subnet_ids      = module.vpc.private_subnets # EKS control plane uses private subnets


# The Access fixes (github actions and aws user)
    authentication_mode                         = "API_AND_CONFIG_MAP"
    enable_cluster_creator_admin_permissions   = true

# ilya
    access_entries = {
      ilya_local = {
        principal_arn     = "arn:aws:iam::219127327432:user/ilya"
        policy_associations = {
            admin = {
                policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
                access_scope = { type = "cluster" }
            }
        }
    }
# kevinb
      kevinb_local = {
        principal_arn     = "arn:aws:iam::219127327432:user/kevinb"
        policy_associations = {
            admin = {
                policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
                access_scope = { type = "cluster" }
            }
        }      
    }
}    
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
