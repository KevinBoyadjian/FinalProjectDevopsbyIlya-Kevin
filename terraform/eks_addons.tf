# ---------------------------------------------------------------------------------------------------------------------
# AWS LOAD BALANCER CONTROLLER - IAM INFRASTRUCTURE (IRSA)
# ---------------------------------------------------------------------------------------------------------------------

# 1. Define the Trust Policy
# This allows the EKS OIDC provider to assume this specific IAM role
data "aws_iam_policy_document" "lb_controller_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"
     principals {
      type        = "Federated"
      identifiers = [module.eks_cluster.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      # This strips the 'https://' from the OIDC URL to match the required AWS format
      variable = "${replace(module.eks_cluster.cluster_oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks_cluster.cluster_oidc_issuer_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

# 2. Create the IAM Role for the Controller
resource "aws_iam_role" "lb_controller" {
  name               = "${var.project_name}-lb-controller-role"
  assume_role_policy = data.aws_iam_policy_document.lb_controller_assume_role_policy.json
  tags = var.common_tags
}


# 3. Attach the AWS-MANAGED POLICY to the IAM Role
# This is the correct way to grant permissions to the ALB Controller.
resource "aws_iam_role_policy_attachment" "lb_controller_attach" {
  role       = aws_iam_role.lb_controller.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSLoadBalancerControllerPolicy"
}

# ---------------------------------------------------------------------------------------------------------------------
# NEW ADDITION: TIME SLEEP RESOURCE TO HANDLE IAM PROPAGATION
# ---------------------------------------------------------------------------------------------------------------------
# Force Terraform to wait 60 seconds after the policy is attached
# to ensure AWS IAM has fully propagated before Helm tries to use it.
resource "time_sleep" "wait_for_iam" {
  depends_on      = [aws_iam_role_policy_attachment.lb_controller_attach]
  create_duration = "60s"


# ---------------------------------------------------------------------------------------------------------------------
# AWS LOAD BALANCER CONTROLLER - HELM INSTALLATION
# ---------------------------------------------------------------------------------------------------------------------

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.2"

  depends_on = [time_sleep.wait_for_iam]

  set {
    name  = "clusterName"
    value = module.eks_cluster.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.lb_controller.arn
  }

  set {
    name  = "region"
    value = var.aws_region
  }

  set {
    name  = "vpcId"
    value = module.vpc.vpc_id
  }
}
