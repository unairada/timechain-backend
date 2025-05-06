
variable "ecr_repository_url" {
    default = "782046927010.dkr.ecr.us-east-2.amazonaws.com/timechain-backend"
}

variable "image_tag" {
    default = "e53a2be388ff9c319aac99b58a02aafa690cfc2a"
}


data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group for the ALB (internet-facing)
resource "aws_security_group" "alb_sg" {
  name   = "alb-sg" # TODO: change name if desired
  vpc_id = data.aws_vpc.default.id

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

# Security Group for ECS tasks (only allow traffic from ALB)
resource "aws_security_group" "ecs_task_sg" {
  name   = "timechain-backend-sg" # TODO: change name if desired
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port       = 80 # container port
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "Timechain-Backend-ECS-Exec-Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# Attach AWS-managed policy for pulling from ECR & sending logs
resource "aws_iam_role_policy_attachment" "ecs_task_execution_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "main-ecs-cluster"
}

# Task Definition (point to your ECR image)
resource "aws_ecs_task_definition" "timechain" {
  family                   = "timechain"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name         = "timechain-backend"
      image        = "${var.ecr_repository_url}:${var.image_tag}"
    #   image        = "782046927010.dkr.ecr.us-east-2.amazonaws.com/timechain-backend:e53a2be388ff9c319aac99b58a02aafa690cfc2a" # TODO: point to your ECR repo
      portMappings = [{ containerPort = 80, protocol = "tcp" }]
      essential    = true
    }
  ])
}

# Application Load Balancer
resource "aws_lb" "timechain-backend" {
  name               = "timechain-backend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids
}

# Target Group for ECS
resource "aws_lb_target_group" "timechain-backend" {
  name        = "timechain-backend-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# Listener for ALB
resource "aws_lb_listener" "timechain-backend" {
  load_balancer_arn = aws_lb.timechain-backend.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.timechain-backend.arn
  }
}

# ECS Service
resource "aws_ecs_service" "timechain" {
  name            = "timechain-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.timechain.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_task_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.timechain-backend.arn
    container_name   = "timechain-backend" # must match container_definitions
    container_port   = 80
  }

  depends_on = [aws_lb_listener.timechain-backend]
}
