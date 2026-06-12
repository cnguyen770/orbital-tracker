output "ec2_public_ip" {
  description = "Public IP of the orbital tracker backend"
  value       = aws_instance.orbital_tracker.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the orbital tracker backend"
  value       = aws_instance.orbital_tracker.public_dns
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.orbital_tracker.domain_name
}

output "frontend_bucket" {
  description = "S3 bucket name for the frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_website_endpoint" {
  description = "S3 static website endpoint"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}
