# ---------------------------------------------------------------------------------------------------------------------
# AWS LOAD BALANCER CONTROLLER - HELM INSTALLATION
# ---------------------------------------------------------------------------------------------------------------------

resource "null_resource" "aws_lb_controller_crds" {
  triggers = {
    cluster_name = data.terraform_remote_state.core.outputs.cluster_name
  }

  provisioner "local-exec" {
    command = <<EOT
      aws eks update-kubeconfig --name ${data.terraform_remote_state.core.outputs.cluster_name} --region us-east-1
      kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/helm/aws-load-balancer-controller/crds/crds.yaml
    EOT  
    working_dir = path.cwd 
  }
}

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.2"
  skip_crds  = true

  depends_on = [null_resource.aws_lb_controller_crds]

  set {
    name  = "clusterName"
    value = data.terraform_remote_state.core.outputs.cluster_name
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
    value = data.terraform_remote_state.core.outputs.lb_controller_role_arn
  }
  set {
    name  = "region"
    value = "us-east-1"
  }
  set {
    name  = "vpcId"
    value = data.terraform_remote_state.core.outputs.vpc_id
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# EXTERNAL DNS - HELM INSTALLATION
# ---------------------------------------------------------------------------------------------------------------------

resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns/"
  chart      = "external-dns"
  namespace  = "kube-system"
  version    = "1.13.1"

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = data.terraform_remote_state.core.outputs.external_dns_role_arn
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

  depends_on = [helm_release.lb_controller]
}
