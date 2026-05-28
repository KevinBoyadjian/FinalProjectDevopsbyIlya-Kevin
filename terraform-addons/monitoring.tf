resource "kubernetes_secret" "grafana_admin_password" {
  metadata {
    name      = "grafana-admin-password" # Standard name for this secret
    namespace = data.terraform_remote_state.core.outputs.monitoring_namespace
  }
  data = {
    "admin-password" = var.grafana_admin_password # This pulls the value from your TF_VAR_
    "admin-user"     = "admin"
  }
  type = "Opaque"
}


# 2. IAM INFRASTRUCTURE FOR PROMETHEUS (IRSA)
# This creates the "Key" that allows Prometheus to talk to AWS
data "aws_iam_policy_document" "prometheus_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"
    principals {
      type        = "Federated"
      identifiers = [data.terraform_remote_state.core.outputs.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(data.terraform_remote_state.core.outputs.cluster_oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:monitoring:kube-prometheus-stack-prometheus"]
    }
  }
}

resource "aws_iam_role" "prometheus_role" {
  name               = "${data.terraform_remote_state.core.outputs.project_name}-prometheus-role"
  assume_role_policy = data.aws_iam_policy_document.prometheus_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "prometheus_read_only" {
  role       = aws_iam_role.prometheus_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

# 3. Deploy the Kube-Prometheus-Stack (Prometheus + Grafana + Node Exporter)
resource "helm_release" "prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = data.terraform_remote_state.core.outputs.monitoring_namespace  
  version    = "51.0.0"

  wait = false

  depends_on = [
    kubernetes_secret.grafana_admin_password 
    # Add other dependencies here if needed
  ]


    # --- PROMETHEUS IAM ROLE (IRSA) ---
  set {
    name  = "prometheus.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.prometheus_role.arn
  }

  set {
    name  = "prometheus.serviceAccount.create"
    value = "true"
  }

  set {
    name  = "prometheus.serviceAccount.name"
    value = "kube-prometheus-stack-prometheus"
  }

    # --- OPTIMIZATION FOR T3.MEDIUM NODES ---
  set {
    name  = "prometheus.prometheusSpec.resources.requests.memory"
    value = "512Mi"
  }

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "1d"
  }

    # --- GRAFANA CONFIGURATION ---
  set {
    name  = "grafana.enabled"
    value = "true"
  }

  set {
    name  = "grafana.admin.existingSecret"
    value = kubernetes_secret.grafana_admin_password.metadata[0].name # Reference the new Secret resource
  }
  set {
    name  = "grafana.admin.passwordKey"
    value = "admin-password" # This matches the key defined in the kubernetes_secret resource
  }
  
  set {
    name  = "grafana.admin.userKey"
    value = "admin-user" 
  }

  set {
    name  = "grafana.ingress.enabled"
    value = "false"
  }
}


# 4. Create the AWS Load Balancer for the Grafana Dashboard
resource "kubernetes_ingress_v1" "grafana_ingress" {
  metadata {
    name        = "grafana-ingress"
    namespace   = data.terraform_remote_state.core.outputs.monitoring_namespace
    annotations = {
      "alb.ingress.kubernetes.io/scheme"          = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"     = "ip"
      "alb.ingress.kubernetes.io/subnet-tags"     = "kubernetes.io/role/elb=1"
      "external-dns.alpha.kubernetes.io/hostname" = "grafana.top5score.com"
    }
  }

  spec {
    ingress_class_name = "alb"
    rule {
      host = "grafana.top5score.com"
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = "kube-prometheus-stack-grafana"
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }

  # --- THE SMOOTHNESS FIXES ---
  # 1. Don't let Terraform hang waiting for AWS to delete the ALB
  wait_for_load_balancer = false

  # THE AUTOMATION HOOK:
  # This runs automatically during 'terraform destroy'
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl patch ingress ${self.metadata[0].name} -n ${self.metadata[0].namespace} -p '{\"metadata\":{\"finalizers\":null}}' --type=merge || true"
  }

  # 2. Ensures Ingress is created AFTER the app, and deleted BEFORE the app
  depends_on = [helm_release.prometheus_stack]
}
