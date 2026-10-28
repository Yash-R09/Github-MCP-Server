terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "project" {
  type    = string
  default = "github-mcp-server"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project
      ManagedBy = "terraform"
    }
  }
}

# Where the Docker image will be stored
resource "aws_ecr_repository" "app" {
  name         = var.project
  force_delete = true # lets 'terraform destroy' work even when images exist

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep only the 5 newest images so storage doesn't grow
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# The ECS cluster (a logical group; Fargate tasks run inside it)
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"
}

# Where container logs will go (CloudWatch)
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project}"
  retention_in_days = 7
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}