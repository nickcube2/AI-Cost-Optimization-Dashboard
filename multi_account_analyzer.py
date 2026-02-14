#!/usr/bin/env python3
"""
Multi-Account Cost Analyzer
============================

Extends the base cost optimizer with multi-account support.
Analyzes costs across dev/staging/prod environments.

Author: Nicholas Awuni
"""

import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class MultiAccountAnalyzer:
    """
    Analyzes AWS costs across multiple accounts.
    
    Supports:
    - Multiple AWS profiles
    - Cross-account IAM roles
    - Consolidated billing analysis
    - Per-account recommendations
    """
    
    def __init__(self, accounts_config: str, region: str = 'us-east-1'):
        """
        Initialize multi-account analyzer.
        
        Args:
            accounts_config: Comma-separated account configs
                            Format: "name:profile" or "name:role_arn"
            region: AWS region for Cost Explorer
        """
        self.region = region
        self.accounts = self._parse_accounts(accounts_config)
        
    def _parse_accounts(self, config: str) -> List[Tuple[str, str]]:
        """
        Parse account configuration string.
        
        Args:
            config: "prod:default,staging:staging-profile,dev:dev-profile"
        
        Returns:
            List of (account_name, profile_name) tuples
        """
        accounts = []
        
        if not config or config.strip() == '':
            # Default to single account
            return [('default', 'default')]
        
        for account_str in config.split(','):
            account_str = account_str.strip()
            if ':' in account_str:
                name, profile = account_str.split(':', 1)
                accounts.append((name.strip(), profile.strip()))
            else:
                # If no profile specified, use account name as profile
                accounts.append((account_str.strip(), account_str.strip()))
        
        return accounts
    
    def get_client_for_account(self, profile_name: str):
        """
        Get Cost Explorer client for specific account.
        
        Args:
            profile_name: AWS profile name or role ARN
        
        Returns:
            boto3 Cost Explorer client
        """
        try:
            # If it's a role ARN, assume role
            if profile_name.startswith('arn:aws:iam::'):
                sts = boto3.client('sts')
                assumed_role = sts.assume_role(
                    RoleArn=profile_name,
                    RoleSessionName='CostOptimizerSession'
                )
                
                credentials = assumed_role['Credentials']
                return boto3.client(
                    'ce',
                    region_name=self.region,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            else:
                # Use named profile
                session = boto3.Session(profile_name=profile_name)
                return session.client('ce', region_name=self.region)
                
        except Exception as e:
            print(f"   ⚠️  Could not create client for {profile_name}: {str(e)[:50]}")
            return None
    
    def get_multi_account_costs(self, days: int = 7) -> Dict:
        """
        Fetch costs for all configured accounts.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with per-account cost data
        """
        print(f"\n🏢 Analyzing {len(self.accounts)} account(s)...")
        
        results = {
            'accounts': {},
            'total_all_accounts': 0.0,
            'period_days': days,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        end_str = end_date.strftime('%Y-%m-%d')
        start_str = start_date.strftime('%Y-%m-%d')
        
        results['start_date'] = start_str
        results['end_date'] = end_str
        
        for account_name, profile in self.accounts:
            print(f"\n📊 Fetching costs for: {account_name}")
            
            client = self.get_client_for_account(profile)
            if not client:
                results['accounts'][account_name] = {'error': 'Failed to create client'}
                continue
            
            try:
                response = client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_str,
                        'End': end_str
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'SERVICE'
                        }
                    ]
                )
                
                # Process results
                total_cost = 0.0
                costs_by_service = {}
                daily_costs = []
                
                for day_result in response['ResultsByTime']:
                    day_date = day_result['TimePeriod']['Start']
                    day_total = 0.0
                    
                    for group in day_result['Groups']:
                        service_name = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        
                        day_total += cost
                        costs_by_service[service_name] = costs_by_service.get(service_name, 0) + cost
                    
                    daily_costs.append({
                        'date': day_date,
                        'cost': round(day_total, 2)
                    })
                    
                    total_cost += day_total
                
                # Sort services by cost
                sorted_services = {
                    service: round(cost, 2)
                    for service, cost in sorted(
                        costs_by_service.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                }
                
                results['accounts'][account_name] = {
                    'total_cost': round(total_cost, 2),
                    'by_service': sorted_services,
                    'daily_costs': daily_costs,
                    'top_service': list(sorted_services.keys())[0] if sorted_services else 'N/A',
                    'service_count': len(sorted_services)
                }
                
                results['total_all_accounts'] += total_cost
                
                print(f"   ✅ ${round(total_cost, 2)} total ({len(sorted_services)} services)")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                results['accounts'][account_name] = {
                    'error': str(e),
                    'total_cost': 0.0
                }
        
        results['total_all_accounts'] = round(results['total_all_accounts'], 2)
        
        print(f"\n💰 Combined Total: ${results['total_all_accounts']}")
        
        return results
    
    def compare_accounts(self, multi_account_data: Dict) -> str:
        """
        Generate AI analysis comparing costs across accounts.
        
        Args:
            multi_account_data: Output from get_multi_account_costs()
        
        Returns:
            Comparative analysis text
        """
        # Build comparison summary
        summary = f"""
Multi-Account AWS Cost Analysis ({multi_account_data['period_days']} days)
Period: {multi_account_data['start_date']} to {multi_account_data['end_date']}
Combined Total: ${multi_account_data['total_all_accounts']:.2f}

Per-Account Breakdown:
"""
        
        accounts = multi_account_data['accounts']
        total = multi_account_data['total_all_accounts']
        
        for account_name, data in accounts.items():
            if 'error' in data and 'total_cost' not in data:
                summary += f"\n{account_name}: ERROR - {data['error']}\n"
                continue
            
            cost = data['total_cost']
            percentage = (cost / total * 100) if total > 0 else 0
            
            summary += f"\n{account_name}:\n"
            summary += f"  - Total: ${cost:.2f} ({percentage:.1f}% of combined)\n"
            summary += f"  - Services: {data.get('service_count', 0)}\n"
            summary += f"  - Top Service: {data.get('top_service', 'N/A')}\n"
            
            # Show top 3 services
            if 'by_service' in data:
                summary += f"  - Top 3 Costs:\n"
                for i, (service, svc_cost) in enumerate(list(data['by_service'].items())[:3], 1):
                    summary += f"    {i}. {service}: ${svc_cost:.2f}\n"
        
        return summary
    
    def generate_cross_account_recommendations(self, multi_account_data: Dict) -> List[Dict]:
        """
        Generate recommendations comparing accounts.
        
        Args:
            multi_account_data: Cost data from all accounts
        
        Returns:
            List of cross-account optimization opportunities
        """
        recommendations = []
        
        accounts = multi_account_data['accounts']
        
        # Find cost imbalances
        costs = [(name, data.get('total_cost', 0)) for name, data in accounts.items()]
        costs.sort(key=lambda x: x[1], reverse=True)
        
        if len(costs) >= 2:
            highest = costs[0]
            lowest = costs[-1]
            
            if highest[1] > 0 and lowest[1] > 0:
                ratio = highest[1] / lowest[1]
                
                if ratio > 3:
                    recommendations.append({
                        'type': 'cost_imbalance',
                        'severity': 'medium',
                        'title': f'{highest[0]} costs {ratio:.1f}x more than {lowest[0]}',
                        'description': f'Investigate if workload distribution is appropriate',
                        'accounts_affected': [highest[0], lowest[0]]
                    })
        
        # Find duplicate services across accounts
        service_presence = {}
        for account_name, data in accounts.items():
            if 'by_service' not in data:
                continue
            
            for service in data['by_service'].keys():
                if service not in service_presence:
                    service_presence[service] = []
                service_presence[service].append(account_name)
        
        # Services in all accounts
        all_accounts = set(accounts.keys())
        for service, present_in in service_presence.items():
            if len(present_in) == len(all_accounts) and len(all_accounts) > 1:
                recommendations.append({
                    'type': 'shared_service_opportunity',
                    'severity': 'low',
                    'title': f'{service} used in all accounts',
                    'description': 'Consider shared/centralized resources to reduce duplicate costs',
                    'service': service,
                    'accounts_affected': present_in
                })
        
        return recommendations


def print_multi_account_summary(data: Dict):
    """
    Print formatted multi-account cost summary.
    
    Args:
        data: Multi-account cost data
    """
    print("\n" + "=" * 70)
    print("🏢 MULTI-ACCOUNT COST SUMMARY")
    print("=" * 70 + "\n")
    
    print(f"Period: {data['start_date']} to {data['end_date']}")
    print(f"Combined Total: ${data['total_all_accounts']:.2f}\n")
    
    # Sort accounts by cost
    sorted_accounts = sorted(
        data['accounts'].items(),
        key=lambda x: x[1].get('total_cost', 0),
        reverse=True
    )
    
    print("Per-Account Breakdown:")
    print("-" * 70)
    
    for i, (account_name, account_data) in enumerate(sorted_accounts, 1):
        if 'error' in account_data and 'total_cost' not in account_data:
            print(f"{i}. {account_name}: ❌ ERROR")
            continue
        
        cost = account_data.get('total_cost', 0)
        percentage = (cost / data['total_all_accounts'] * 100) if data['total_all_accounts'] > 0 else 0
        services = account_data.get('service_count', 0)
        top_service = account_data.get('top_service', 'N/A')
        
        print(f"{i}. {account_name}:")
        print(f"   Cost: ${cost:.2f} ({percentage:.1f}%)")
        print(f"   Services: {services}")
        print(f"   Top: {top_service}")
        
        # Mini bar chart
        if data['total_all_accounts'] > 0:
            bar_length = int((cost / data['total_all_accounts']) * 40)
            bar = "█" * bar_length
            print(f"   {bar}")
        print()
    
    print("=" * 70 + "\n")


# Example usage
if __name__ == "__main__":
    # Test multi-account analyzer
    accounts_config = os.getenv('AWS_ACCOUNTS', 'default:default')
    
    analyzer = MultiAccountAnalyzer(accounts_config)
    results = analyzer.get_multi_account_costs(days=7)
    
    print_multi_account_summary(results)
    
    # Generate cross-account recommendations
    recs = analyzer.generate_cross_account_recommendations(results)
    
    if recs:
        print("\n🔍 Cross-Account Insights:")
        for rec in recs:
            print(f"  • {rec['title']}")
            print(f"    {rec['description']}")