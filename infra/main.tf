# Target Groups - Fixed for Fargate compatibility
resource "aws_lb_target_group" "frontend" {
  name_prefix = "pdf-f-"  # Use name_prefix to allow replacements
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # Changed from "instance" to "ip" for Fargate compatibility

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
    create_before_destroy = true  # Allow replacement without deletion errors
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-frontend-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "backend" {
  name_prefix = "pdf-b-"  # Use name_prefix to allow replacements
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # Changed from "instance" to "ip" for Fargate compatibility

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
    create_before_destroy = true  # Allow replacement without deletion errors
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backend-tg"
    Environment = var.environment
  }
}