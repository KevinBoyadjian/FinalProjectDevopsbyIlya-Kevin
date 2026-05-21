terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket = "ilyakevin-project-tf-state"
    # CRITICAL: This is a different key than the Core!
    key    = "state/addons.tfstate" 
    region = "us-east-1"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# The Magic: Read the "Memory" of the Core layer
data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = "ilyakevin-project-tf-state"
    key    = "state/core.tfstate" # This matches the key we just set in the Core folder
    region = "us-east-1"
  }
}

# Use the data from 'Core' to log into Kubernetes
provider "kubernetes" {
  host                   = data.terraform_remote_state.core.outputs.cluster_endpoint
  cluster_ca_certificate = base64decode(data.terraform_remote_state.core.outputs.cluster_certificate_authority_data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", data.terraform_remote_state.core.outputs.cluster_name]
    command     = "aws"
  }
}

provider "helm" {
  kubernetes {
    host                   = data.terraform_remote_state.core.outputs.cluster_endpoint
    cluster_ca_certificate = base64decode(data.terraform_remote_state.core.outputs.cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", data.terraform_remote_state.core.outputs.cluster_name]
      command     = "aws"
    }
  }
}

