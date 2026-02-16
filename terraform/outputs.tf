output "ecr_repository_url" {
  description = "ECR repository URL for dashboard image pushes"
  value       = aws_ecr_repository.dashboard.repository_url
}

output "alb_dns_name" {
  description = "Public ALB DNS name for the dashboard"
  value       = aws_lb.dashboard.dns_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.dashboard.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.dashboard.name
}
