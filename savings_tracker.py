#!/usr/bin/env python3
"""
Savings Tracker & ROI Measurement
==================================

Tracks implemented optimizations and measures actual $ saved.

Author: Nicholas Awuni
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

class SavingsTracker:
    """
    Tracks cost optimization recommendations and actual savings achieved.
    """
    
    def __init__(self, db_path: str = 'data/savings_tracker.db'):
        """
        Initialize savings tracker with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create data directory if needed
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_date TEXT NOT NULL,
                account_name TEXT,
                recommendation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                estimated_monthly_savings REAL,
                risk_level TEXT,
                effort TEXT,
                status TEXT DEFAULT 'pending',
                implemented_date TEXT,
                actual_monthly_savings REAL,
                notes TEXT
            )
        ''')
        
        # Cost snapshots table (for measuring actual impact)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                account_name TEXT,
                total_cost REAL NOT NULL,
                period_days INTEGER,
                service_breakdown TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_recommendation(self, 
                          title: str,
                          recommendation_type: str,
                          estimated_savings: float,
                          account_name: str = 'default',
                          description: str = '',
                          risk_level: str = 'medium',
                          effort: str = 'medium') -> int:
        """
        Add a new cost optimization recommendation.
        
        Args:
            title: Recommendation title
            recommendation_type: Type (e.g., 'EC2_rightsizing', 'S3_lifecycle')
            estimated_savings: Estimated monthly $ savings
            account_name: AWS account name
            description: Detailed description
            risk_level: low/medium/high
            effort: quick_win/medium/complex
        
        Returns:
            Recommendation ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recommendations 
            (created_date, account_name, recommendation_type, title, description,
             estimated_monthly_savings, risk_level, effort, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            account_name,
            recommendation_type,
            title,
            description,
            estimated_savings,
            risk_level,
            effort
        ))
        
        rec_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return rec_id
    
    def mark_implemented(self, 
                        rec_id: int,
                        actual_savings: Optional[float] = None,
                        notes: str = '') -> bool:
        """
        Mark a recommendation as implemented.
        
        Args:
            rec_id: Recommendation ID
            actual_savings: Actual monthly savings measured (optional)
            notes: Implementation notes
        
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE recommendations
            SET status = 'implemented',
                implemented_date = ?,
                actual_monthly_savings = ?,
                notes = ?
            WHERE id = ?
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            actual_savings,
            notes,
            rec_id
        ))
        
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def mark_rejected(self, rec_id: int, reason: str = '') -> bool:
        """
        Mark a recommendation as rejected/won't implement.
        
        Args:
            rec_id: Recommendation ID
            reason: Rejection reason
        
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE recommendations
            SET status = 'rejected',
                notes = ?
            WHERE id = ?
        ''', (reason, rec_id))
        
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def add_cost_snapshot(self,
                         total_cost: float,
                         account_name: str = 'default',
                         period_days: int = 7,
                         service_breakdown: Optional[Dict] = None) -> int:
        """
        Record a cost snapshot for trend analysis.
        
        Args:
            total_cost: Total cost for period
            account_name: AWS account name
            period_days: Period analyzed
            service_breakdown: Dict of service costs
        
        Returns:
            Snapshot ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cost_snapshots
            (snapshot_date, account_name, total_cost, period_days, service_breakdown)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            account_name,
            total_cost,
            period_days,
            json.dumps(service_breakdown) if service_breakdown else None
        ))
        
        snapshot_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return snapshot_id
    
    def get_roi_summary(self) -> Dict:
        """
        Calculate ROI from implemented recommendations.
        
        Returns:
            ROI summary with total savings, implementation rate, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all recommendations
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'implemented' THEN 1 ELSE 0 END) as implemented,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(estimated_monthly_savings) as total_estimated,
                SUM(CASE WHEN status = 'implemented' THEN estimated_monthly_savings ELSE 0 END) as implemented_estimated,
                SUM(CASE WHEN status = 'implemented' AND actual_monthly_savings IS NOT NULL 
                    THEN actual_monthly_savings ELSE 0 END) as total_actual
            FROM recommendations
        ''')
        
        row = cursor.fetchone()
        
        total = row[0] or 0
        implemented = row[1] or 0
        rejected = row[2] or 0
        pending = row[3] or 0
        total_estimated = row[4] or 0
        implemented_estimated = row[5] or 0
        total_actual = row[6] or 0
        
        implementation_rate = (implemented / total * 100) if total > 0 else 0
        
        # Calculate accuracy (actual vs estimated for implemented items)
        cursor.execute('''
            SELECT 
                estimated_monthly_savings,
                actual_monthly_savings
            FROM recommendations
            WHERE status = 'implemented' AND actual_monthly_savings IS NOT NULL
        ''')
        
        accuracy_data = cursor.fetchall()
        
        if accuracy_data:
            total_diff = sum(abs(est - act) for est, act in accuracy_data)
            avg_diff = total_diff / len(accuracy_data)
            accuracy = 100 - (avg_diff / (sum(est for est, _ in accuracy_data) / len(accuracy_data)) * 100)
        else:
            accuracy = 0
        
        conn.close()
        
        return {
            'total_recommendations': total,
            'implemented': implemented,
            'rejected': rejected,
            'pending': pending,
            'implementation_rate': round(implementation_rate, 1),
            'total_estimated_savings': round(total_estimated, 2),
            'implemented_estimated_savings': round(implemented_estimated, 2),
            'total_actual_savings': round(total_actual, 2),
            'forecast_accuracy': round(accuracy, 1),
            'annual_projected_savings': round(total_actual * 12, 2)
        }
    
    def get_recommendations(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get all recommendations, optionally filtered by status.
        
        Args:
            status: Filter by status (pending/implemented/rejected)
        
        Returns:
            List of recommendation dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM recommendations
                WHERE status = ?
                ORDER BY created_date DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT * FROM recommendations
                ORDER BY created_date DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_cost_trend(self, account_name: str = 'default', limit: int = 30) -> List[Dict]:
        """
        Get historical cost snapshots for trend analysis.
        
        Args:
            account_name: AWS account name
            limit: Number of snapshots to retrieve
        
        Returns:
            List of cost snapshots
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cost_snapshots
            WHERE account_name = ?
            ORDER BY snapshot_date DESC
            LIMIT ?
        ''', (account_name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        snapshots = []
        for row in rows:
            snapshot = dict(row)
            if snapshot['service_breakdown']:
                snapshot['service_breakdown'] = json.loads(snapshot['service_breakdown'])
            snapshots.append(snapshot)
        
        return snapshots


def print_roi_dashboard(roi_data: Dict):
    """
    Print formatted ROI dashboard.
    
    Args:
        roi_data: Output from get_roi_summary()
    """
    print("\n" + "=" * 70)
    print("💰 SAVINGS TRACKER - ROI DASHBOARD")
    print("=" * 70 + "\n")
    
    print("📊 Recommendations Summary:")
    print(f"   Total: {roi_data['total_recommendations']}")
    print(f"   ✅ Implemented: {roi_data['implemented']}")
    print(f"   ⏳ Pending: {roi_data['pending']}")
    print(f"   ❌ Rejected: {roi_data['rejected']}")
    print(f"   📈 Implementation Rate: {roi_data['implementation_rate']}%\n")
    
    print("💵 Financial Impact:")
    print(f"   Estimated Savings (All): ${roi_data['total_estimated_savings']:.2f}/month")
    print(f"   Implemented Savings: ${roi_data['implemented_estimated_savings']:.2f}/month")
    print(f"   Actual Savings: ${roi_data['total_actual_savings']:.2f}/month")
    print(f"   Annual Projection: ${roi_data['annual_projected_savings']:.2f}/year\n")
    
    if roi_data['forecast_accuracy'] > 0:
        print(f"🎯 Forecast Accuracy: {roi_data['forecast_accuracy']:.1f}%")
    
    print("\n" + "=" * 70 + "\n")


# Example usage
if __name__ == "__main__":
    # Initialize tracker
    tracker = SavingsTracker()
    
    # Add example recommendations
    rec1 = tracker.add_recommendation(
        title="Downsize EC2 i3.2xlarge to t3.large",
        recommendation_type="EC2_rightsizing",
        estimated_savings=320.0,
        description="Instance running at 8% CPU utilization",
        risk_level="low",
        effort="quick_win"
    )
    
    rec2 = tracker.add_recommendation(
        title="Delete old RDS snapshot from 2023",
        recommendation_type="RDS_cleanup",
        estimated_savings=45.0,
        description="Manual snapshot no longer needed",
        risk_level="low",
        effort="quick_win"
    )
    
    # Mark one as implemented
    tracker.mark_implemented(rec1, actual_savings=310.0, notes="Resized during maintenance window")
    
    # Add cost snapshot
    tracker.add_cost_snapshot(
        total_cost=850.0,
        account_name='default',
        period_days=7,
        service_breakdown={'EC2': 500.0, 'RDS': 200.0, 'S3': 150.0}
    )
    
    # Show ROI dashboard
    roi = tracker.get_roi_summary()
    print_roi_dashboard(roi)
    
    # Show pending recommendations
    pending = tracker.get_recommendations(status='pending')
    if pending:
        print("⏳ Pending Recommendations:")
        for rec in pending:
            print(f"  • {rec['title']} - Est. ${rec['estimated_monthly_savings']:.2f}/month")