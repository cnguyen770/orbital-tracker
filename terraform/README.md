# Terraform

Infrastructure as code for the orbital tracker's AWS resources. The infrastructure was originally provisioned manually through the AWS console — these files codify that setup so the environment is reproducible from scratch with `terraform apply`.

This only covers orbital tracker resources. The portfolio site has its own separate infrastructure.

---

## What's Here

- `main.tf` — provider configuration (AWS, us-east-1)
- `variables.tf` — instance type, key pair name, region
- `network.tf` — VPC and subnet variables referencing existing infrastructure
- `ec2.tf` — t3.micro EC2 instance and security group (ports 22, 80, 443, 8000)
- `s3.tf` — S3 bucket for the React frontend with static website hosting
- `cloudfront.tf` — CloudFront distribution routing `/api/*` to EC2 and `/*` to S3
- `outputs.tf` — EC2 IP, CloudFront domain, S3 endpoint

---

## How the Routing Works

Both the frontend and backend share a single CloudFront distribution. `/api/*` requests get forwarded to the EC2 instance running the FastAPI backend. Everything else serves the static React build from S3. This avoids mixed content issues without needing a custom domain or separate SSL certificates.

---

## State

Terraform state is not committed to the repo. Before running `terraform apply` on a fresh machine you'd want to configure a remote backend (S3 + DynamoDB is the standard approach) so state is shared and locked. For a solo project, local state works fine.

---

## Usage

```bash
cd terraform

# install the AWS provider
terraform init

# preview what would be created
terraform plan

# apply (provisions real AWS resources — costs money)
terraform apply
```

The existing live infrastructure was not imported into state, these files describe what would be created on a fresh deploy. Running `terraform apply` against a new AWS account would reproduce the full orbital tracker environment.
