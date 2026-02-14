#!/usr/bin/env python3
"""
Auto-Remediation Engine
=======================

Automatically generates Terraform code to implement cost optimizations.

Author: Nicholas Awuni
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

class AutoRemediator:
    """
    Generates Terraform code for implementing cost optimizations.
    Uses AI to create production-ready infrastructure-as-code.
    """
    
    def __init__(self, claude_api_key: str, dry_run: bool = True):
        """
        Initialize auto-remediation engine.
        
        Args:
            claude_api_key: Anthropic API key
            dry_run: If True, only show what would change (don't apply)
        """
        self.client = Anthropic(api_key=claude_api_key) if claude_api_key else None
        self.dry_run = dry_run
    
    def generate_terraform_for_optimization(self, 
                                           optimization_type: str,
                                           details: Dict) -> str:
        """
        Generate Terraform code for a specific optimization.
        
        Args:
            optimization_type: Type of optimization (EC2_resize, EBS_delete, etc.)
            details: Optimization details (instance IDs, target sizes, etc.)
        
        Returns:
            Generated Terraform code
        """
        if not self.client:
            return "# Error: Claude API key not configured"
        
        # Build prompt based on optimization type
        prompt = self._build_terraform_prompt(optimization_type, details)
        
        try:
            print(f"🤖 Generating Terraform code for: {optimization_type}...")
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            terraform_code = message.content[0].text
            
            # Clean up - remove markdown code fences if present
            if terraform_code.startswith('```terraform'):
                terraform_code = terraform_code.replace('```terraform\n', '', 1)
                terraform_code = terraform_code.replace('```hcl\n', '', 1)
                terraform_code = terraform_code.rsplit('```', 1)[0]
            
            print("   ✅ Terraform code generated")
            
            return terraform_code
            
        except Exception as e:
            return f"# Error generating Terraform: {str(e)}"
    
    def _build_terraform_prompt(self, optimization_type: str, details: Dict) -> str:
        """Build AI prompt for Terraform generation."""
        
        base_prompt = """You are a Terraform expert. Generate production-ready Terraform code for this AWS cost optimization.

REQUIREMENTS:
- Use Terraform AWS provider
- Include all necessary resource blocks
- Add comments explaining the change
- Include data sources if needed
- Follow Terraform best practices
- Make it idempotent and safe
"""
        
        if optimization_type == 'EC2_resize':
            prompt = base_prompt + f"""

OPTIMIZATION: Resize EC2 instance

Details:
- Current instance ID: {details.get('instance_id', 'i-XXXXXXXXX')}
- Current type: {details.get('current_type', 't2.micro')}
- Target type: {details.get('target_type', 't3.small')}
- Reason: {details.get('reason', 'Right-sizing based on usage')}

Generate Terraform code that:
1. Uses data source to reference existing instance
2. Modifies instance_type
3. Includes depends_on if needed
4. Adds lifecycle block to prevent accidental deletion
5. Comments explaining the change and expected savings

Output ONLY valid Terraform HCL code, no explanations before or after.
"""
        
        elif optimization_type == 'EBS_delete':
            prompt = base_prompt + f"""

OPTIMIZATION: Delete unused EBS volumes

Details:
- Volume IDs: {details.get('volume_ids', [])}
- Reason: {details.get('reason', 'Unattached for >30 days')}
- Total size: {details.get('total_gb', 0)} GB

Generate Terraform code that:
1. Creates null_resource with local-exec provisioner
2. Uses AWS CLI to delete volumes (safer than terraform destroy)
3. Includes confirmation check (manual approval step)
4. Comments explaining what will be deleted

Output ONLY valid Terraform HCL code, no explanations before or after.
"""
        
        elif optimization_type == 'RDS_snapshot_delete':
            prompt = base_prompt + f"""

OPTIMIZATION: Delete old RDS snapshots

Details:
- Snapshot IDs: {details.get('snapshot_ids', [])}
- Age: {details.get('age_days', 0)} days
- Reason: {details.get('reason', 'Automated cleanup of aged snapshots')}

Generate Terraform code that:
1. Uses null_resource with local-exec
2. AWS CLI commands to delete snapshots
3. Includes date check (only delete if >90 days old)
4. Dry-run option

Output ONLY valid Terraform HCL code, no explanations before or after.
"""
        
        elif optimization_type == 'S3_lifecycle':
            prompt = base_prompt + f"""

OPTIMIZATION: Add S3 lifecycle policy

Details:
- Bucket name: {details.get('bucket_name', 'example-bucket')}
- Current storage class: {details.get('current_class', 'STANDARD')}
- Target class: {details.get('target_class', 'INTELLIGENT_TIERING')}
- Transition days: {details.get('transition_days', 30)}

Generate Terraform code that:
1. References existing S3 bucket via data source
2. Creates aws_s3_bucket_lifecycle_configuration resource
3. Implements tiering rules (STANDARD → INTELLIGENT_TIERING → GLACIER)
4. Includes expiration for old versions
5. Comments explaining cost impact

Output ONLY valid Terraform HCL code, no explanations before or after.
"""
        
        else:
            prompt = base_prompt + f"""

OPTIMIZATION: {optimization_type}

Details: {details}

Generate appropriate Terraform code for this optimization.
Output ONLY valid Terraform HCL code, no explanations before or after.
"""
        
        return prompt
    
    def save_terraform_file(self, code: str, filename: str, directory: str = 'terraform_generated') -> str:
        """
        Save generated Terraform code to file.
        
        Args:
            code: Terraform code
            filename: File name (e.g., 'ec2_resize.tf')
            directory: Output directory
        
        Returns:
            Full path to saved file
        """
        os.makedirs(directory, exist_ok=True)
        
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        return filepath
    
    def validate_terraform(self, filepath: str) -> Dict:
        """
        Run terraform validate on generated code.
        
        Args:
            filepath: Path to .tf file
        
        Returns:
            Validation results
        """
        import subprocess
        
        directory = os.path.dirname(filepath)
        
        # Initialize Terraform
        init_result = subprocess.run(
            ['terraform', 'init'],
            cwd=directory,
            capture_output=True,
            text=True
        )
        
        if init_result.returncode != 0:
            return {
                'valid': False,
                'stage': 'init',
                'error': init_result.stderr
            }
        
        # Validate
        validate_result = subprocess.run(
            ['terraform', 'validate'],
            cwd=directory,
            capture_output=True,
            text=True
        )
        
        return {
            'valid': validate_result.returncode == 0,
            'stage': 'validate',
            'output': validate_result.stdout,
            'error': validate_result.stderr if validate_result.returncode != 0 else None
        }
    
    def create_remediation_plan(self, recommendations: List[Dict]) -> List[Dict]:
        """
        Create auto-remediation plan for low-risk recommendations.
        
        Args:
            recommendations: List of cost optimization recommendations
        
        Returns:
            List of actionable remediation steps
        """
        plan = []
        
        for rec in recommendations:
            # Only auto-remediate low-risk items
            if rec.get('risk', '').lower() != 'low':
                continue
            
            # Only quick wins
            if rec.get('effort', '').lower() not in ['quick_win', 'quick win', '<1 hour']:
                continue
            
            # Map recommendation to remediation
            if 'ebs' in rec.get('title', '').lower() and 'delete' in rec.get('title', '').lower():
                plan.append({
                    'recommendation_id': rec.get('id'),
                    'optimization_type': 'EBS_delete',
                    'details': {
                        'volume_ids': rec.get('resource_ids', []),
                        'reason': rec.get('description', '')
                    },
                    'auto_safe': True
                })
            
            elif 'snapshot' in rec.get('title', '').lower() and 'delete' in rec.get('title', '').lower():
                plan.append({
                    'recommendation_id': rec.get('id'),
                    'optimization_type': 'RDS_snapshot_delete',
                    'details': {
                        'snapshot_ids': rec.get('resource_ids', []),
                        'reason': rec.get('description', '')
                    },
                    'auto_safe': True
                })
            
            elif 's3' in rec.get('title', '').lower() and 'lifecycle' in rec.get('title', '').lower():
                plan.append({
                    'recommendation_id': rec.get('id'),
                    'optimization_type': 'S3_lifecycle',
                    'details': {
                        'bucket_name': rec.get('resource_id', ''),
                        'current_class': 'STANDARD',
                        'target_class': 'INTELLIGENT_TIERING',
                        'transition_days': 30
                    },
                    'auto_safe': True
                })
        
        return plan


def print_remediation_plan(plan: List[Dict]):
    """
    Print formatted auto-remediation plan.
    
    Args:
        plan: Output from create_remediation_plan()
    """
    print("\n" + "=" * 70)
    print("🔧 AUTO-REMEDIATION PLAN")
    print("=" * 70 + "\n")
    
    if not plan:
        print("No low-risk quick wins available for auto-remediation.\n")
        print("Consider implementing medium-risk or complex optimizations manually.")
        return
    
    print(f"Found {len(plan)} optimization(s) suitable for auto-remediation:\n")
    
    for i, item in enumerate(plan, 1):
        print(f"{i}. {item['optimization_type']}")
        print(f"   Recommendation ID: {item.get('recommendation_id', 'N/A')}")
        print(f"   Auto-safe: {'✅ Yes' if item['auto_safe'] else '⚠️  No'}")
        
        details = item['details']
        if 'volume_ids' in details:
            print(f"   Volumes: {len(details['volume_ids'])}")
        elif 'snapshot_ids' in details:
            print(f"   Snapshots: {len(details['snapshot_ids'])}")
        elif 'bucket_name' in details:
            print(f"   Bucket: {details['bucket_name']}")
        
        print()
    
    print("=" * 70 + "\n")


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize remediator
    claude_key = os.getenv('CLAUDE_API_KEY')
    remediator = AutoRemediator(claude_key, dry_run=True)
    
    # Example: Generate Terraform for EC2 resize
    optimization = {
        'instance_id': 'i-0123456789abcdef0',
        'current_type': 't2.large',
        'target_type': 't3.medium',
        'reason': 'CPU utilization <10% for 30 days. Downsize will save $50/month.'
    }
    
    terraform_code = remediator.generate_terraform_for_optimization(
        'EC2_resize',
        optimization
    )
    
    print("\n" + "=" * 70)
    print("🔧 GENERATED TERRAFORM CODE")
    print("=" * 70 + "\n")
    print(terraform_code)
    print("\n" + "=" * 70 + "\n")
    
    # Save to file
    filepath = remediator.save_terraform_file(
        terraform_code,
        'ec2_resize_example.tf'
    )
    
    print(f"💾 Saved to: {filepath}\n")
    print("⚠️  DRY RUN MODE: No changes will be applied.")
    print("To apply: cd terraform_generated && terraform plan && terraform apply\n")