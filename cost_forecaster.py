#!/usr/bin/env python3
"""
AI-Powered Cost Forecasting
============================

Uses Claude AI to predict future AWS costs based on historical trends.

Author: Nicholas Awuni
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List
import json
from anthropic import Anthropic

class CostForecaster:
    """
    Predicts future AWS costs using AI analysis of historical trends.
    """
    
    def __init__(self, claude_api_key: str):
        """
        Initialize forecaster with Claude API.
        
        Args:
            claude_api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=claude_api_key) if claude_api_key else None
    
    def analyze_trend(self, daily_costs: List[Dict]) -> Dict:
        """
        Analyze cost trend from daily data.
        
        Args:
            daily_costs: List of {'date': 'YYYY-MM-DD', 'cost': float}
        
        Returns:
            Trend analysis with statistics
        """
        if not daily_costs or len(daily_costs) < 7:
            return {
                'trend': 'insufficient_data',
                'average_daily': 0,
                'growth_rate': 0
            }
        
        # Calculate statistics
        costs = [day['cost'] for day in daily_costs]
        
        average_daily = sum(costs) / len(costs)
        
        # Simple linear trend (first half vs second half)
        mid_point = len(costs) // 2
        first_half_avg = sum(costs[:mid_point]) / mid_point
        second_half_avg = sum(costs[mid_point:]) / (len(costs) - mid_point)
        
        if first_half_avg > 0:
            growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        else:
            growth_rate = 0
        
        # Determine trend direction
        if abs(growth_rate) < 5:
            trend = 'stable'
        elif growth_rate > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        # Calculate volatility (standard deviation)
        mean = average_daily
        variance = sum((x - mean) ** 2 for x in costs) / len(costs)
        std_dev = variance ** 0.5
        
        volatility = (std_dev / mean * 100) if mean > 0 else 0
        
        return {
            'trend': trend,
            'average_daily': round(average_daily, 2),
            'growth_rate': round(growth_rate, 2),
            'volatility': round(volatility, 2),
            'min_daily': round(min(costs), 2),
            'max_daily': round(max(costs), 2),
            'total_period': round(sum(costs), 2)
        }
    
    def forecast_with_ai(self, cost_data: Dict, forecast_days: int = 30) -> str:
        """
        Generate AI-powered cost forecast.
        
        Args:
            cost_data: Historical cost data
            forecast_days: Number of days to forecast
        
        Returns:
            AI-generated forecast analysis
        """
        if not self.client:
            return "⚠️ Claude API key not configured. Cannot generate AI forecast."
        
        # Analyze historical trend
        if 'daily_costs' not in cost_data:
            return "⚠️ Insufficient historical data for forecasting."
        
        trend_analysis = self.analyze_trend(cost_data['daily_costs'])
        
        # Build prompt for Claude
        prompt = f"""You are a FinOps forecasting expert. Analyze this AWS cost data and provide a forecast.

HISTORICAL DATA ({cost_data.get('period_days', 0)} days):
- Total Spend: ${cost_data.get('total_cost', 0):.2f}
- Average Daily: ${trend_analysis['average_daily']:.2f}
- Trend: {trend_analysis['trend']} ({trend_analysis['growth_rate']:+.1f}% growth rate)
- Volatility: {trend_analysis['volatility']:.1f}%
- Range: ${trend_analysis['min_daily']:.2f} - ${trend_analysis['max_daily']:.2f} per day

TOP SERVICES:
"""
        
        # Add top 5 services
        if 'by_service' in cost_data:
            for i, (service, cost) in enumerate(list(cost_data['by_service'].items())[:5], 1):
                percentage = (cost / cost_data['total_cost'] * 100) if cost_data['total_cost'] > 0 else 0
                prompt += f"{i}. {service}: ${cost:.2f} ({percentage:.1f}%)\n"
        
        prompt += f"""

FORECAST REQUIREMENTS:
Provide a {forecast_days}-day cost forecast with:

1. **PREDICTED SPEND**
   - Projected total for next {forecast_days} days
   - Confidence level (High/Medium/Low)
   - Key assumptions

2. **TREND ANALYSIS**
   - Will costs increase, decrease, or stay stable?
   - Why? (seasonal patterns, growth trends, anomalies)
   - Risk factors that could change the forecast

3. **BUDGET ALERT**
   - If current trend continues, when will you hit $X milestones?
   - Monthly run rate projection
   - Comparison to current spend

4. **RECOMMENDATIONS**
   - Actions to take if forecast is accurate
   - Early warning signs to watch for
   - Cost control measures

Be specific with dollar amounts and dates. Explain your reasoning.
Format clearly with headers and bullet points.
"""
        
        try:
            print("🔮 Generating AI-powered forecast...")
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            forecast = message.content[0].text
            
            print("   ✅ Forecast generated")
            
            return forecast
            
        except Exception as e:
            return f"❌ Error generating forecast: {str(e)}"
    
    def simple_forecast(self, cost_data: Dict, forecast_days: int = 30) -> Dict:
        """
        Generate simple statistical forecast (no AI).
        
        Args:
            cost_data: Historical cost data
            forecast_days: Days to forecast
        
        Returns:
            Forecast data with predictions
        """
        if 'daily_costs' not in cost_data or len(cost_data['daily_costs']) < 7:
            return {
                'error': 'Insufficient data for forecasting',
                'min_days_required': 7
            }
        
        trend = self.analyze_trend(cost_data['daily_costs'])
        
        # Simple projection: average daily cost * forecast days
        # Adjusted for growth trend
        avg_daily = trend['average_daily']
        growth_rate = trend['growth_rate'] / 100  # Convert to decimal
        
        # Project with linear growth
        projected_daily = avg_daily * (1 + (growth_rate / 2))  # Dampen extreme growth
        
        forecast_total = projected_daily * forecast_days
        
        # Calculate monthly run rate
        monthly_run_rate = projected_daily * 30
        
        # Determine confidence
        if trend['volatility'] < 10:
            confidence = 'High'
        elif trend['volatility'] < 25:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        return {
            'forecast_days': forecast_days,
            'projected_total': round(forecast_total, 2),
            'projected_daily_avg': round(projected_daily, 2),
            'monthly_run_rate': round(monthly_run_rate, 2),
            'confidence': confidence,
            'trend': trend['trend'],
            'growth_rate': trend['growth_rate'],
            'volatility': trend['volatility'],
            'assumptions': [
                f"Based on {len(cost_data['daily_costs'])} days of historical data",
                f"Assumes {trend['trend']} trend continues",
                f"Current growth rate: {trend['growth_rate']:+.1f}%",
                f"Volatility: {trend['volatility']:.1f}%"
            ]
        }
    
    def budget_alert(self, cost_data: Dict, monthly_budget: float) -> Dict:
        """
        Check if forecast exceeds budget and when.
        
        Args:
            cost_data: Historical cost data
            monthly_budget: Monthly budget threshold
        
        Returns:
            Alert information
        """
        forecast = self.simple_forecast(cost_data, forecast_days=30)
        
        if 'error' in forecast:
            return forecast
        
        projected_monthly = forecast['monthly_run_rate']
        
        if projected_monthly > monthly_budget:
            overage = projected_monthly - monthly_budget
            overage_pct = (overage / monthly_budget) * 100
            
            # Estimate when budget will be exceeded
            daily_avg = forecast['projected_daily_avg']
            days_to_budget = int(monthly_budget / daily_avg) if daily_avg > 0 else 30
            
            alert_date = datetime.now() + timedelta(days=days_to_budget)
            
            return {
                'alert': True,
                'severity': 'high' if overage_pct > 20 else 'medium',
                'monthly_budget': monthly_budget,
                'projected_spend': projected_monthly,
                'overage': round(overage, 2),
                'overage_percent': round(overage_pct, 1),
                'days_until_exceeded': days_to_budget,
                'estimated_date': alert_date.strftime('%Y-%m-%d'),
                'recommendation': f"Take action now to reduce daily spend by ${(overage/30):.2f}/day"
            }
        else:
            buffer = monthly_budget - projected_monthly
            buffer_pct = (buffer / monthly_budget) * 100
            
            return {
                'alert': False,
                'severity': 'low',
                'monthly_budget': monthly_budget,
                'projected_spend': projected_monthly,
                'buffer': round(buffer, 2),
                'buffer_percent': round(buffer_pct, 1),
                'status': 'On track - within budget'
            }


def print_forecast_summary(forecast_data: Dict):
    """
    Print formatted forecast summary.
    
    Args:
        forecast_data: Output from simple_forecast()
    """
    if 'error' in forecast_data:
        print(f"\n⚠️  {forecast_data['error']}")
        return
    
    print("\n" + "=" * 70)
    print("🔮 COST FORECAST")
    print("=" * 70 + "\n")
    
    print(f"Forecast Period: Next {forecast_data['forecast_days']} days")
    print(f"Confidence Level: {forecast_data['confidence']}\n")
    
    print(f"📊 Projected Spend: ${forecast_data['projected_total']:.2f}")
    print(f"📈 Daily Average: ${forecast_data['projected_daily_avg']:.2f}")
    print(f"📅 Monthly Run Rate: ${forecast_data['monthly_run_rate']:.2f}")
    print(f"📉 Trend: {forecast_data['trend']} ({forecast_data['growth_rate']:+.1f}%)")
    print(f"🎲 Volatility: {forecast_data['volatility']:.1f}%\n")
    
    print("Assumptions:")
    for assumption in forecast_data['assumptions']:
        print(f"  • {assumption}")
    
    print("\n" + "=" * 70 + "\n")


def print_budget_alert(alert_data: Dict):
    """
    Print budget alert information.
    
    Args:
        alert_data: Output from budget_alert()
    """
    if 'error' in alert_data:
        return
    
    print("\n" + "=" * 70)
    
    if alert_data['alert']:
        print("⚠️  BUDGET ALERT")
        print("=" * 70 + "\n")
        
        severity_emoji = "🔴" if alert_data['severity'] == 'high' else "🟡"
        print(f"{severity_emoji} Severity: {alert_data['severity'].upper()}\n")
        
        print(f"Monthly Budget: ${alert_data['monthly_budget']:.2f}")
        print(f"Projected Spend: ${alert_data['projected_spend']:.2f}")
        print(f"Overage: ${alert_data['overage']:.2f} ({alert_data['overage_percent']:.1f}% over budget)\n")
        
        print(f"⏰ Estimated to exceed budget in: {alert_data['days_until_exceeded']} days")
        print(f"📅 Date: {alert_data['estimated_date']}\n")
        
        print(f"💡 Recommendation: {alert_data['recommendation']}")
        
    else:
        print("✅ BUDGET STATUS: ON TRACK")
        print("=" * 70 + "\n")
        
        print(f"Monthly Budget: ${alert_data['monthly_budget']:.2f}")
        print(f"Projected Spend: ${alert_data['projected_spend']:.2f}")
        print(f"Buffer: ${alert_data['buffer']:.2f} ({alert_data['buffer_percent']:.1f}% under budget)\n")
        
        print(f"✓ {alert_data['status']}")
    
    print("\n" + "=" * 70 + "\n")


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    import sys
    
    load_dotenv()
    
    # Mock cost data for testing
    mock_data = {
        'total_cost': 100.50,
        'period_days': 30,
        'by_service': {
            'Amazon EC2': 50.25,
            'Amazon S3': 25.10,
            'AWS Lambda': 15.05
        },
        'daily_costs': [
            {'date': '2026-01-09', 'cost': 3.20},
            {'date': '2026-01-10', 'cost': 3.35},
            {'date': '2026-01-11', 'cost': 3.42},
            # ... more days
            {'date': '2026-02-07', 'cost': 3.55},
            {'date': '2026-02-08', 'cost': 3.60}
        ]
    }
    
    # Initialize forecaster
    claude_key = os.getenv('CLAUDE_API_KEY')
    forecaster = CostForecaster(claude_key)
    
    # Generate simple forecast
    forecast = forecaster.simple_forecast(mock_data, forecast_days=30)
    print_forecast_summary(forecast)
    
    # Check budget
    budget_check = forecaster.budget_alert(mock_data, monthly_budget=120.0)
    print_budget_alert(budget_check)
    
    # AI forecast (if API key available)
    if claude_key and '--ai' in sys.argv:
        ai_forecast = forecaster.forecast_with_ai(mock_data, forecast_days=30)
        print("\n" + "=" * 70)
        print("🤖 AI-POWERED FORECAST")
        print("=" * 70 + "\n")
        print(ai_forecast)