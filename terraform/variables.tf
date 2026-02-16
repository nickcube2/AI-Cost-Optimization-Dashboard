variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "ai-cost-dashboard"
}

variable "vpc_id" {
  description = "VPC ID for ALB and ECS service"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB and Fargate tasks"
  type        = list(string)
}

variable "container_port" {
  description = "Container port exposed by Flask app"
  type        = number
  default     = 5000
}

variable "task_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Fargate task memory (MiB)"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Number of ECS tasks"
  type        = number
  default     = 1
}

variable "container_image" {
  description = "Full container image URI. If empty, ECR repo output is used with image_tag."
  type        = string
  default     = ""
}

variable "image_tag" {
  description = "Container image tag used when container_image is empty"
  type        = string
  default     = "latest"
}

variable "dashboard_mode" {
  description = "Dashboard mode passed to the container"
  type        = string
  default     = "demo"
}

variable "llm_provider" {
  description = "LLM provider passed to the container"
  type        = string
  default     = "openai"
}

variable "openai_model" {
  description = "OpenAI model name passed to the container"
  type        = string
  default     = "gpt-4.1-mini"
}

variable "dashboard_api_token" {
  description = "Token required by dashboard API endpoints"
  type        = string
  default     = ""
  sensitive   = true
}
