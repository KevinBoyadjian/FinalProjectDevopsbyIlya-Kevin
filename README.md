# Football Live Scores Platform - DevSecOps Final Project

## Overview

This project is a complete DevSecOps final project based on a football live scores web application.

The application is built with Python Flask and allows users to view live football scores, upcoming fixtures, and match details for several major football competitions. It also includes FIFA World Cup 2026 fixtures stored locally in a JSON file.

The project is not only focused on application development. It also demonstrates a full DevSecOps lifecycle, including Docker containerization, security scanning, Infrastructure as Code, Kubernetes deployment, cloud infrastructure, CI/CD automation, and controlled manual deployment using GitHub Actions.

## Main Features

The platform currently supports:

* English Premier League
* Spanish La Liga
* Italian Serie A
* French Ligue 1
* German Bundesliga
* UEFA Champions League
* FIFA World Cup 2026

The application can display:

* Live matches
* Upcoming matches
* Match details
* Match status
* Scores
* Kick-off time
* Stadium and city
* Group and stage information for FIFA World Cup 2026
* Events and lineups when available

## FIFA World Cup 2026 Feature

The FIFA World Cup 2026 fixtures are stored locally in a JSON file instead of being loaded from an external API.

The file is located at:

```text
app/data/world-cup-2026.json
```

This design was chosen for several reasons:

* The World Cup schedule is mostly static before the tournament starts.
* It avoids consuming unnecessary external API quota.
* The application can still display World Cup fixtures even if the external API is unavailable.
* It improves reliability for a school project demonstration.

The JSON file contains the 2026 World Cup fixtures with:

* Match ID
* Match number
* Competition name
* Stage
* Group
* Home team
* Away team
* Scores
* Match status
* Kick-off time
* Time zone
* Stadium
* City
* Events
* Lineups

For matches that have not started yet, the score is empty and the application displays the match as an upcoming fixture.

## Project Goals

The main goal of this project is to demonstrate a complete DevSecOps workflow.

The project covers:

* Application development with Python Flask
* Source control with Git and GitHub
* Feature branch workflow
* Docker image creation
* Container security scanning
* Infrastructure provisioning with Terraform
* Kubernetes deployment on AWS EKS
* Manual CI/CD deployment with GitHub Actions
* Secrets management
* Rollback strategy
* Cloud resource cleanup

## Technology Stack

### Backend

* Python 3.12
* Flask
* Jinja2
* Requests
* Gunicorn

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 templates

### DevOps

* Git
* GitHub
* GitHub Actions
* Docker
* Docker Hub

### Cloud and Infrastructure

* AWS
* Amazon EKS
* IAM
* OIDC authentication
* Terraform
* Kubernetes
* CloudFront
* Application Load Balancer

### Security

* Bandit
* Trivy
* GitHub Secrets
* Kubernetes Security Context
* Non-root Docker container user
* Kubernetes readiness and liveness probes

## Architecture

```text
User
 |
 | HTTPS
 v
CloudFront / Domain
 |
 v
AWS Load Balancer
 |
 v
Amazon EKS Cluster
 |
 v
Kubernetes Service
 |
 v
Kubernetes Deployment
 |
 v
Football App Pods
 |
 v
Flask Application
 |
 +--> External football API for live and upcoming league matches
 |
 +--> Local JSON file for FIFA World Cup 2026 fixtures
```

## Repository Structure

```text
FinalProjectDevops/
├── .github/
│   └── workflows/
│       ├── pipeline.yml
│       ├── terraform-core.yml
│       └── terraformaddons.yml
│
├── app/
│   ├── app.py
│   ├── config.py
│   ├── data/
│   │   └── world-cup-2026.json
│   ├── services/
│   │   └── football_api.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       ├── index.html
│       └── match.html
│
├── data/
│
├── docker/
│   └── Dockerfile
│
├── k8s/
│   └── manifests/
│
├── terraform-addons/
│
├── terraform-core/
│
├── requirements.txt
└── README.md
```

## Application Routes

### Home Page

```text
/
```

Displays the application home page and league selection.

### League Matches

```text
/?league=premier-league
/?league=la-liga
/?league=serie-a
/?league=ligue-1
/?league=bundesliga
/?league=champions-league
/?league=world-cup-2026
```

The application first tries to display live matches.

If no live match is available, it displays upcoming matches.

### Match Details

```text
/match/<match_id>
```

Displays details for a selected match.

For FIFA World Cup 2026 matches, the details page can display:

* Teams
* Match status
* Kick-off time
* Stage
* Group
* Stadium
* City
* Events when available
* Lineups when available

### API Endpoint

```text
/api/live?league=<league_key>
```

Returns match data in JSON format.

### Health Check

```text
/health
```

Returns:

```text
OK
```

This endpoint is used by Kubernetes liveness and readiness probes.

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/KevinBoyadjian/FinalProjectDevops.git
cd FinalProjectDevops
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

For local development, the application can use environment variables.

Example:

```bash
export SECRET_KEY="dev-secret-key"
export FOOTBALL_API_KEY="your-api-key"
export FOOTBALL_API_BASE_URL="https://v3.football.api-sports.io"
export SEASON="2025"
```

The FIFA World Cup 2026 page does not require an external API key because it reads from the local JSON file.

### 5. Run the Application Locally

```bash
python app/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

To test the World Cup page:

```text
http://127.0.0.1:5000/?league=world-cup-2026
```

To test a match details page:

```text
http://127.0.0.1:5000/match/260001
```

To test the health endpoint:

```text
http://127.0.0.1:5000/health
```

## Docker

The application is containerized using Docker.

The Dockerfile is located at:

```text
docker/Dockerfile
```

The image uses a multi-stage build:

1. Builder stage: installs Python dependencies.
2. Runtime stage: copies only the required application files and installed dependencies.

The final container runs with a non-root user for security.

### Build the Docker Image

The build must be executed from the root of the repository:

```bash
docker build -f docker/Dockerfile -t football-app:test .
```

The final dot is important because it defines the Docker build context.

The Dockerfile needs access to:

```text
requirements.txt
app/
```

If the build is launched from inside the `docker/` folder, Docker will not find these files.

### Verify the World Cup JSON Exists in the Container

```bash
docker run --rm football-app:test ls -la /app/data
```

Expected file:

```text
world-cup-2026.json
```

### Run the Container Locally

```bash
docker run --rm -p 5000:5000 \
  -e SECRET_KEY="dev-secret-key" \
  -e FOOTBALL_API_KEY="dummy" \
  -e FOOTBALL_API_BASE_URL="https://v3.football.api-sports.io" \
  football-app:test
```

Then open:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/?league=world-cup-2026
http://127.0.0.1:5000/health
```

## Kubernetes

The Kubernetes manifests are stored in:

```text
k8s/manifests/
```

The Kubernetes deployment includes:

* 3 application replicas
* RollingUpdate deployment strategy
* Resource requests and limits
* Liveness probe
* Readiness probe
* Non-root container execution
* Kubernetes Secret usage for sensitive variables

The application runs on port:

```text
5000
```

The `/health` route is used by Kubernetes to verify that the container is alive and ready to receive traffic.

## Terraform

The project separates infrastructure into two Terraform parts.

### terraform-core

The `terraform-core` directory manages the main infrastructure.

It is responsible for core cloud resources such as the EKS cluster and related base infrastructure.

Workflow file:

```text
.github/workflows/terraform-core.yml
```

Supported actions:

```text
plan
apply
destroy
```

### terraform-addons

The `terraform-addons` directory manages additional infrastructure components and Kubernetes-related add-ons.

Workflow file:

```text
.github/workflows/terraformaddons.yml
```

Supported actions:

```text
plan
apply
destroy
```

The destroy action in the add-ons workflow also cleans Kubernetes resources such as Ingresses and LoadBalancer services before destroying the Terraform resources. This helps avoid orphaned AWS resources.

## GitHub Actions

The project uses GitHub Actions for CI/CD and infrastructure operations.

The workflows are manually triggered using:

```yaml
workflow_dispatch:
```

This means deployments do not run automatically on every push.

This choice is important for this project because it helps:

* Avoid accidental deployments
* Control AWS costs
* Keep infrastructure creation under manual control
* Make the project safer for a final school demonstration

## Main DevSecOps Pipeline

Workflow file:

```text
.github/workflows/pipeline.yml
```

The main pipeline contains three main jobs.

### Job 1: Python Security Scan

This job performs a Python security scan using Bandit.

Main steps:

* Checkout repository
* Install Python
* Install Bandit
* Scan the `app/` directory

Command:

```bash
bandit -r app/ -s B104
```

`B104` is skipped because the Flask application intentionally binds to `0.0.0.0` for container and Kubernetes usage.

### Job 2: Build, Scan, and Push Docker Image

This job:

* Logs in to Docker Hub using GitHub Secrets
* Builds the Docker image
* Tags the image with the GitHub commit SHA
* Tags the image as `latest`
* Scans the Docker image using Trivy
* Pushes the image to Docker Hub if the scan succeeds

Using the commit SHA as an image tag improves traceability because each image can be linked to a specific Git commit.

### Job 3: Deploy to Kubernetes

This job:

* Checks out the repository
* Installs Terraform CLI
* Authenticates to AWS using GitHub OIDC
* Reads the EKS cluster name from Terraform output
* Updates the kubeconfig file
* Creates or updates Kubernetes Secrets
* Applies Kubernetes manifests
* Updates the Kubernetes deployment image
* Invalidates the CloudFront cache

## Required GitHub Secrets

The following GitHub Secrets are required for the workflows:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
AWS_TERRAFORM_ROLE_ARN
FOOTBALL_API_KEY
FOOTBALL_API_BASE_URL
SECRET_KEY
ALB_HANDSHAKE_SECRET
GRAFANA_ADMIN_PASSWORD
```

A future multi-provider API improvement may also use:

```text
FOOTBALL_DATA_API_KEY
```

Secrets must never be committed to Git and must never be printed in application logs.

## Security Practices

This project includes several DevSecOps security practices:

* Python code scanning with Bandit
* Docker image scanning with Trivy
* Secrets stored in GitHub Secrets
* AWS authentication through OIDC instead of static AWS keys
* Non-root user inside the Docker container
* Kubernetes security context
* Kubernetes readiness and liveness probes
* API error handling to avoid application crashes
* Manual workflows to prevent accidental cloud deployments

## Deployment Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/world-cup-2026
```

### 2. Test Locally

```bash
python app/app.py
```

### 3. Test Docker Build

```bash
docker build -f docker/Dockerfile -t football-app:test .
```

### 4. Commit Changes

Example:

```bash
git add README.md app/app.py app/config.py app/services/football_api.py app/templates/index.html app/templates/match.html app/data/world-cup-2026.json
git commit -m "Add FIFA World Cup 2026 fixtures from local JSON"
```

### 5. Push the Branch

```bash
git push -u origin feature/world-cup-2026
```

### 6. Open a Pull Request

Create a Pull Request from:

```text
feature/world-cup-2026
```

to:

```text
main
```

### 7. Run the Manual GitHub Actions Workflow

After validation, the deployment workflow can be launched manually from the GitHub Actions tab.

## Rollback Strategy

### Pull Request Not Merged Yet

If the Pull Request has not been merged, the `main` branch is not affected.

The feature branch can be fixed with new commits or the Pull Request can simply be closed.

### Revert a Merged Pull Request

If a Pull Request was merged and caused a problem, a revert can be created from GitHub.

This creates a new commit that reverses the previous change.

### Kubernetes Rollback

If the application deployment fails or behaves incorrectly in Kubernetes:

```bash
kubectl rollout history deployment/football-app-deployment
kubectl rollout undo deployment/football-app-deployment
kubectl rollout status deployment/football-app-deployment
```

### Docker Image Rollback

Because images are tagged with the GitHub commit SHA, an older image can be redeployed if needed:

```bash
kubectl set image deployment/football-app-deployment football-app=<dockerhub-username>/football-app:<previous-commit-sha>
```

## Destroy Procedure

Since this project creates cloud infrastructure, resources should be destroyed when they are no longer needed.

Recommended destroy order:

```text
1. Destroy add-ons
2. Destroy core infrastructure
```

### Step 1: Destroy Add-ons

Run the `terraformaddons.yml` workflow manually with:

```text
action = destroy
```

This removes add-ons and cleans Kubernetes resources such as Ingresses and LoadBalancer services.

### Step 2: Destroy Core Infrastructure

Run the `terraform-core.yml` workflow manually with:

```text
action = destroy
```

This destroys the core infrastructure, including the EKS cluster and related resources.

## Troubleshooting

### Docker Build Cannot Find requirements.txt or app/

Make sure the Docker build command is executed from the root of the repository:

```bash
cd FinalProjectDevops
docker build -f docker/Dockerfile -t football-app:test .
```

Do not run the build from inside the `docker/` directory.

### API Returns 403 Invalid API Key

This means the external API key is missing, invalid, or expired.

The FIFA World Cup 2026 page should still work because it uses the local JSON file.

### FIFA World Cup 2026 Fixtures Do Not Appear

Check that the JSON file exists at:

```text
app/data/world-cup-2026.json
```

Also verify that the Docker image contains it:

```bash
docker run --rm football-app:test ls -la /app/data
```

### Match Details Show Empty Events or Lineups

For upcoming matches, events and lineups may not exist yet.

The application displays a message explaining that they will appear closer to kick-off or after the match starts.

### Kubernetes Pods Do Not Update

Check the rollout:

```bash
kubectl rollout status deployment/football-app-deployment
kubectl get pods
kubectl describe pod <pod-name>
```

If needed, manually update the deployment image:

```bash
kubectl set image deployment/football-app-deployment football-app=<image>:<tag>
```

## Final Project Explanation

This project demonstrates the full lifecycle of a DevSecOps application.

The application starts as a Python Flask web application, then it is containerized with Docker, scanned for security issues, pushed to Docker Hub, and deployed to Kubernetes on AWS EKS.

Terraform is used to manage infrastructure as code, and GitHub Actions is used to automate security checks, image building, vulnerability scanning, and deployment.

The workflows are manual to avoid unnecessary AWS costs and to keep deployment under control during the final project demonstration.

## Future Improvements

Possible future improvements include:

* Football-Data.org fallback API provider
* Match history persistence
* Advanced player statistics
* Prometheus monitoring
* Grafana dashboards
* More advanced alerting
* Automated tests before Docker build
* Better frontend design and competition branding

## Contributors

* Kevin Boyadjian
* Ilya

## About

Live scores website for European football competitions and FIFA World Cup 2026 fixtures, built as a DevSecOps final project.
