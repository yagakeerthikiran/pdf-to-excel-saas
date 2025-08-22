# Use existing VPC by ID (from your AWS discovery)
variable "vpc_id" {
  description = "Existing VPC ID to use"
  type        = string
  default     = "vpc-03d8efc7fc1d488a4"  # From your AWS discovery
}

# Data source to reference existing VPC
data "aws_vpc" "main" {
  id = var.vpc_id
}

# Target Groups - Fixed with data source and safe replacement
resource "aws_lb_target_group" "frontend" {
  name_prefix = "pdf-f-"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"  # For Fargate

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "pdf-excel-saas-prod-frontend-tg"
    Environment = "prod"
  }
}

resource "aws_lb_target_group" "backend" {
  name_prefix = "pdf-b-"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"  # For Fargate

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "pdf-excel-saas-prod-backend-tg"
    Environment = "prod"
  }
}

# Reference existing ALB
data "aws_lb" "main" {
  name = "pdf-excel-saas-prod-alb"
}

# Load Balancer Listeners
resource "aws_lb_listener" "frontend" {
  load_balancer_arn = data.aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.frontend.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health", "/docs"]
    }
  }
}