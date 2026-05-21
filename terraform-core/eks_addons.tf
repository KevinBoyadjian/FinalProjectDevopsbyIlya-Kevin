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

  # This acts as a "Graceful Shutdown" timer.
  # When you run 'destroy', Terraform will wait 30 seconds before 
  # deleting this role, giving the Load Balancer Controller time 
  # to use this role to delete the real ALBs in AWS.
  provisioner "local-exec" {
    when    = destroy
    command = "sleep 30"
  }
}

# 3. This creates a custom IAM Policy using the content of your JSON file
resource "aws_iam_policy" "lb_controller_custom_policy" {
  name        = "${var.project_name}-lb-controller-custom-policy"
  description = "Custom IAM policy for AWS Load Balancer Controller"
  policy      = file("${path.module}/iam_policy_alb.json")

  tags = var.common_tags
}

# 4. This attaches your custom policy to the IAM Role
resource "aws_iam_role_policy_attachment" "lb_controller_attach" {
  role       = aws_iam_role.lb_controller.name
  policy_arn = aws_iam_policy.lb_controller_custom_policy.arn
}

# 5. TIME SLEEP RESOURCE TO HANDLE IAM PROPAGATION
# Force Terraform to wait 60 seconds after the policy is attached
# to ensure AWS IAM has fully propagated before Helm tries to use it.
resource "time_sleep" "wait_for_iam" {
  depends_on      = [aws_iam_role_policy_attachment.lb_controller_attach]
  create_duration = "60s"
}

# ---------------------------------------------------------------------------------------------------------------------
# EXTERNAL DNS - IAM INFRASTRUCTURE (Route53 Automation)
# ---------------------------------------------------------------------------------------------------------------------

# 1. The Permissions: What is the "ExternalDNS" software allowed to do?
resource "aws_iam_policy" "external_dns" {
  name        = "${var.project_name}-external-dns-policy"
  description = "Allow ExternalDNS to update Route53"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["route53:ChangeResourceRecordSets"]
        Resource = ["arn:aws:route53:::hostedzone/Z009328231GYPRN2AA3CY"]
      },
      {
        Effect   = "Allow"
        Action   = ["route53:ListHostedZones", "route53:ListResourceRecordSets"]
        Resource = ["*"]
      }
    ]
  })
}

# 2. The Trust Relationship: Who is allowed to "become" this role?
# This links your EKS Cluster's OIDC provider to the ExternalDNS software.
data "aws_iam_policy_document" "external_dns_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"
    principals {
      type        = "Federated"
      identifiers = [module.eks_cluster.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      # This ensures ONLY the external-dns pod in the kube-system namespace can use this role
      variable = "${replace(module.eks_cluster.cluster_oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:external-dns"]
    }
  }
}

# 3. The Role: The actual "Identity" created in AWS
resource "aws_iam_role" "external_dns" {
  name               = "${var.project_name}-external-dns-role"
  assume_role_policy = data.aws_iam_policy_document.external_dns_assume_role_policy.json
}

# 4. The Attachment: Glue the Permissions (Step 1) to the Role (Step 3)
resource "aws_iam_role_policy_attachment" "external_dns_attach" {
  role       = aws_iam_role.external_dns.name
  policy_arn = aws_iam_policy.external_dns.arn
}


# ---------------------------------------------------------------------------------------------------------------------
# AWS LOAD BALANCER CONTROLLER - HELM INSTALLATION
# ---------------------------------------------------------------------------------------------------------------------

resource "null_resource" "aws_lb_controller_crds" {
  triggers = {
    # FIXED: Using cluster_name for v20 compatibility
    cluster_name = module.eks_cluster.cluster_name
    # timestamp    = timestamp() 
  }

  provisioner "local-exec" {
    command = <<EOT
      # FIXED: Using cluster_name instead of cluster_id
      aws eks update-kubeconfig --name ${module.eks_cluster.cluster_name} --region us-east-1
      kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/helm/aws-load-balancer-controller/crds/crds.yaml
    EOT  
    working_dir = path.cwd 
  }

  depends_on = [
    module.eks_cluster 
  ]
}

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.2"
  
  skip_crds = true

  depends_on = [
    time_sleep.wait_for_iam,
    null_resource.aws_lb_controller_crds
  ]


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

# ---------------------------------------------------------------------------------------------------------------------
# EXTERNAL DNS - HELM INSTALLATION (THE MISSING PIECE)
# ---------------------------------------------------------------------------------------------------------------------

resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns/"
  chart      = "external-dns"
  namespace  = "kube-system"
  version    = "1.13.1"

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.external_dns.arn
  }

  set {
    name  = "serviceAccount.name"
    value = "external-dns"
  }
  set {
    name  = "sources"
    value = "{ingress}"
  }
  set {
    name  = "domainFilters"
    value = "{top5score.com}"
  }
  set {
    name  = "provider"
    value = "aws"
  }


  # Ensure the Load Balancer Controller and IAM are ready first
  depends_on = [
    helm_release.lb_controller,
    aws_iam_role_policy_attachment.external_dns_attach
    ]
  }