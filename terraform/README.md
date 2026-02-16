# Terraform Deployment (ECS Fargate + ALB)

This stack deploys the dashboard to AWS using:
- ECR repository
- ECS Fargate service
- Application Load Balancer
- IAM roles and Cost Explorer access policy

## Prerequisites

1. Terraform `>= 1.5`
2. AWS CLI authenticated to target account
3. Existing VPC and two public subnets

## 1) Configure variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Set at minimum:
- `vpc_id`
- `public_subnet_ids`
- `dashboard_api_token`

## 2) Create infrastructure

```bash
terraform init
terraform plan
terraform apply
```

Capture outputs:
- `ecr_repository_url`
- `alb_dns_name`

## 3) Build and push image to ECR

```bash
AWS_REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO=$(terraform output -raw ecr_repository_url)

aws ecr get-login-password --region "$AWS_REGION" | \
docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$ECR_REPO:latest" ..
docker push "$ECR_REPO:latest"
```

## 4) Roll out new image revision

```bash
terraform apply -var="image_tag=latest"
```

Open the dashboard:
```bash
http://<alb_dns_name>/?token=<dashboard_api_token>
```

## Security notes

1. Move secrets to AWS Secrets Manager or SSM Parameter Store for production.
2. Restrict ALB ingress CIDRs before production rollout.
3. Use HTTPS listener + ACM certificate in production.
