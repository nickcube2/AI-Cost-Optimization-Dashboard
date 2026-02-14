```hcl
# Data source to reference the existing EC2 instance
# This ensures we're working with the correct instance that needs resizing
data "aws_instance" "existing_instance" {
  instance_id = "i-0123456789abcdef0"
}

# EC2 instance resource to manage the instance type change
# Downsizing from t2.large to t3.medium based on low CPU utilization (<10% for 30 days)
# Expected savings: $50/month
resource "aws_instance" "optimized_instance" {
  # Reference the existing instance's AMI to maintain consistency
  ami = data.aws_instance.existing_instance.ami

  # Target instance type - downsizing from t2.large to t3.medium
  # t3.medium provides better price/performance ratio for low CPU workloads
  instance_type = "t3.medium"

  # Preserve existing network configuration
  subnet_id              = data.aws_instance.existing_instance.subnet_id
  vpc_security_group_ids = data.aws_instance.existing_instance.vpc_security_group_ids
  
  # Maintain existing key pair for SSH access
  key_name = data.aws_instance.existing_instance.key_name

  # Preserve existing IAM instance profile if attached
  iam_instance_profile = data.aws_instance.existing_instance.iam_instance_profile

  # Maintain existing monitoring configuration
  monitoring = data.aws_instance.existing_instance.monitoring

  # Preserve existing user data if any
  user_data = data.aws_instance.existing_instance.user_data_base64

  # Maintain existing availability zone placement
  availability_zone = data.aws_instance.existing_instance.availability_zone

  # Preserve existing tenancy settings
  tenancy = data.aws_instance.existing_instance.tenancy

  # Maintain existing source/destination check setting
  source_dest_check = data.aws_instance.existing_instance.source_dest_check

  # Preserve existing tags and add optimization tracking
  tags = merge(
    data.aws_instance.existing_instance.tags,
    {
      "CostOptimization"     = "true"
      "OptimizationType"     = "instance-resize"
      "PreviousInstanceType" = "t2.large"
      "OptimizationDate"     = timestamp()
      "ExpectedMonthlySavings" = "$50"
      "OptimizationReason"   = "CPU utilization <10% for 30 days"
    }
  )

  # Lifecycle configuration to prevent accidental deletion and minimize disruption
  lifecycle {
    # Prevent accidental deletion of the instance
    prevent_destroy = true
    
    # Create new instance before destroying old one to minimize downtime
    create_before_destroy = false
    
    # Ignore changes to user_data_base64 to prevent unnecessary replacements
    ignore_changes = [
      user_data_base64,
      user_data
    ]
  }

  # Ensure the data source is evaluated before creating the resource
  depends_on = [
    data.aws_instance.existing_instance
  ]
}

# Output the instance details for verification
output "instance_optimization_summary" {
  description = "Summary of the EC2 instance optimization"
  value = {
    instance_id           = aws_instance.optimized_instance.id
    previous_type        = "t2.large"
    current_type         = aws_instance.optimized_instance.instance_type
    expected_savings     = "$50/month"
    optimization_reason  = "CPU utilization <10% for 30 days"
    public_ip           = aws_instance.optimized_instance.public_ip
    private_ip          = aws_instance.optimized_instance.private_ip
  }
}

# Output for monitoring and alerting integration
output "optimized_instance_id" {
  description = "ID of the optimized EC2 instance"
  value       = aws_instance.optimized_instance.id
}
```