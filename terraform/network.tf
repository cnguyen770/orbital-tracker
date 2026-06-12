variable "vpc_id" {
  description = "VPC ID where the EC2 instance runs"
  type        = string
  default     = "vpc-0e8309be67fdecea5"
}

variable "subnet_id" {
  description = "Subnet ID for the EC2 instance"
  type        = string
  default     = "subnet-0caa12e8909e3c749"
}
