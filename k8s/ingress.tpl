# k8s/manifests/05-ingress.yml
# Purpose: Manages external HTTP/HTTPS access to services within the cluster.
# It provides advanced routing capabilities (e.g., path-based routing) and
# typically provisions a cloud load balancer (like AWS ALB).

apiVersion: networking.k8s.io/v1 # API version for Ingress objects
kind: Ingress                     # Type of Kubernetes resource: Ingress
metadata:
  name: football-app-ingress # Unique name for this Ingress
  labels:
    app: football-app       # Labels for selection and organization
  annotations:
    # PROD: Specific AWS ALB Ingress Controller annotations
    # Tells AWS to provision an Application Load Balancer that is publicly accessible
    alb.ingress.kubernetes.io/scheme: internet-facing
    
    # Routes traffic directly to the Pod IP addresses (instead of NodePorts),
    # which is more efficient and usually preferred.
    alb.ingress.kubernetes.io/target-type: ip
    
    # To enable automated subnet discovery for the AWS Load Balancer Controller.
    alb.ingress.kubernetes.io/subnet-tags: kubernetes.io/role/elb=1

    # THE MAGIC LINE for top5score.com the "hidden" bridge between the Load Balancer and CloudFront.
    external-dns.alpha.kubernetes.io/hostname: "origin.top5score.com"

    # The secret handshake between CDN and Load Balancer (security_edge)
    alb.ingress.kubernetes.io/conditions.football-app-service: >
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName": "X-Custom-Header", "values":["${secret_header_value}"]}}]


    # Optional: Enable HTTP to HTTPS redirect and specify SSL certificate.
    # Uncomment and replace with your actual ACM certificate ARN when using HTTPS.
    # alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS":443}]'
    # alb.ingress.kubernetes.io/ssl-redirect: '443'
    # alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id
spec:
  ingressClassName: alb # PROD: Specifies that the AWS Load Balancer Controller should manage this Ingress
# 1. The Public Identity (What CloudFront forwards)
  rules:
    - host: "top5score.com"
      http:
        paths:
          - path: / # Route all traffic hitting the root path
            pathType: Prefix # Matches all paths that start with /
            backend:
              service:
                name: football-app-service # Target Kubernetes Service (from 03-service.yaml)
                port:
                  number: 80 # Target port on the Service (from 03-service.yaml)

# 2. The Internal Identity (The "Bridge" name)
    - host: "origin.top5score.com"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: football-app-service
                port:
                  number: 80