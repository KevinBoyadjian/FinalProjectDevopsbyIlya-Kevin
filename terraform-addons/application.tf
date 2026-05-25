# In terraform-addons/application.tf

# This resource processes ingress.tpl and applies it to Kubernetes
resource "null_resource" "football_app_ingress" {
  # Triggers ensure it reruns if the hostname or secret_header_value changes
  triggers = {
    hostname          = "api.top5score.com"
    secret_header_value = "flask-devsecops-Qa@vD6Yu8!@#31oP-DvdcDVAR-7" # Replace with your actual secret
    cluster_name      = data.terraform_remote_state.core.outputs.cluster_name
    
    # Ensure it only applies after external-dns is ready
    external_dns_ready = helm_release.external_dns.id 
    lb_controller_ready = helm_release.lb_controller.id # Ensure LB Controller is also ready
  }

  provisioner "local-exec" {
    command = <<EOT
      # Update kubeconfig to ensure we're targeting the correct cluster
      aws eks update-kubeconfig --name ${data.terraform_remote_state.core.outputs.cluster_name} --region us-east-1
      
      # Render the template and apply it
      kubectl apply -f - <<EOF
      ${templatefile("../k8s/ingress.tpl", { # Relative path to ingress.tpl
        hostname            = "api.top5score.com",
        secret_header_value = var.alb_handshake_secret
      })}
      EOF
    EOT
    working_dir = path.cwd # Execute from terraform-addons directory
  }

  # This ensures the Ingress is applied only after ExternalDNS and LB Controller are fully functional
  depends_on = [
    helm_release.external_dns,
    helm_release.lb_controller,
  ]
}

