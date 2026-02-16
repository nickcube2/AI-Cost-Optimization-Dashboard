terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  image_uri = var.container_image != "" ? var.container_image : "${aws_ecr_repository.dashboard.repository_url}:${var.image_tag}"
}

resource "aws_ecr_repository" "dashboard" {
  name                 = "${var.app_name}-repo"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_ecs_cluster" "dashboard" {
  name = "${var.app_name}-cluster"
}

resource "aws_cloudwatch_log_group" "dashboard" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 14
}

resource "aws_iam_role" "task_execution" {
  name = "${var.app_name}-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task_role" {
  name = "${var.app_name}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "cost_explorer_access" {
  name = "${var.app_name}-cost-explorer-policy"
  role = aws_iam_role.task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_security_group" "alb" {
  name        = "${var.app_name}-alb-sg"
  description = "ALB security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service" {
  name        = "${var.app_name}-service-sg"
  description = "ECS service security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "dashboard" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "dashboard" {
  name        = "${var.app_name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.dashboard.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dashboard.arn
  }
}

resource "aws_ecs_task_definition" "dashboard" {
  family                   = "${var.app_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = var.app_name
      image     = local.image_uri
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "DASHBOARD_HOST", value = "0.0.0.0" },
        { name = "PORT", value = tostring(var.container_port) },
        { name = "DASHBOARD_MODE", value = var.dashboard_mode },
        { name = "LLM_PROVIDER", value = var.llm_provider },
        { name = "OPENAI_MODEL", value = var.openai_model },
        { name = "DASHBOARD_API_TOKEN", value = var.dashboard_api_token }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.dashboard.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "dashboard" {
  name            = "${var.app_name}-service"
  cluster         = aws_ecs_cluster.dashboard.id
  task_definition = aws_ecs_task_definition.dashboard.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.dashboard.arn
    container_name   = var.app_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http]
}
