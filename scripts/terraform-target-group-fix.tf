# Target Groups - Fixed with create_before_destroy lifecycle
resource "aws_lb_target_group" "frontend" {
  name_prefix = "pdf-f-"  # Use name_prefix instead of fixed name
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # For Fargate compatibility

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
    create_before_destroy = true  # Allow replacement without manual deletion
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-frontend-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "backend" {
  name_prefix = "pdf-b-"  # Use name_prefix instead of fixed name
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # For Fargate compatibility

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
    create_before_destroy = true  # Allow replacement without manual deletion
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backend-tg"
    Environment = var.environment
  }
}