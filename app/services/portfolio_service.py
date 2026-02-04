"""
Service for managing portfolio snapshots and trend data
"""
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Dict
from app.models.investment import Investment
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.distribution import EarningsDistribution
import logging

logger = logging.getLogger(__name__)


def create_portfolio_snapshot(user_id: int, db: Session, snapshot_date: date = None) -> PortfolioSnapshot:
    """
    Create a portfolio snapshot for a user at a specific date
    
    Args:
        user_id: User ID
        db: Database session
        snapshot_date: Date for the snapshot (defaults to today)
    
    Returns:
        Created PortfolioSnapshot
    """
    if snapshot_date is None:
        snapshot_date = date.today()
    
    # Check if snapshot already exists for this date
    existing = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id,
        PortfolioSnapshot.snapshot_date == snapshot_date
    ).first()
    
    if existing:
        logger.info(f"Snapshot already exists for user {user_id} on {snapshot_date}")
        return existing
    
    # Get all active investments for this user
    investments = db.query(Investment).filter(Investment.user_id == user_id).all()
    
    if not investments:
        logger.info(f"No investments found for user {user_id}")
        return None
    
    # Calculate totals
    total_initial = sum(inv.initial_value for inv in investments)
    total_current = sum(inv.current_value for inv in investments)
    growth_amount = total_current - total_initial
    growth_percentage = (growth_amount / total_initial * 100) if total_initial > 0 else 0.0
    
    # Get total earnings received up to this date
    total_earnings = db.query(
        func.sum(EarningsDistribution.amount)
    ).filter(
        EarningsDistribution.user_id == user_id,
        EarningsDistribution.distribution_date <= snapshot_date
    ).scalar() or 0.0
    
    # Create snapshot
    snapshot = PortfolioSnapshot(
        user_id=user_id,
        snapshot_date=snapshot_date,
        total_investment_value=total_current,
        total_initial_value=total_initial,
        total_earnings_received=total_earnings,
        growth_percentage=growth_percentage,
        growth_amount=growth_amount,
        active_investments_count=len(investments)
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    logger.info(f"Created portfolio snapshot for user {user_id} on {snapshot_date}")
    return snapshot


def get_portfolio_trend(
    user_id: int,
    db: Session,
    interval: str = "monthly",
    months: int = 6
) -> Dict:
    """
    Get portfolio trend data for charting
    
    Args:
        user_id: User ID
        db: Database session
        interval: "monthly" or "weekly"
        months: Number of months to look back
    
    Returns:
        Dict with trend_labels, trend_values, and metadata
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    # Query snapshots in the date range
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id,
        PortfolioSnapshot.snapshot_date >= start_date,
        PortfolioSnapshot.snapshot_date <= end_date
    ).order_by(PortfolioSnapshot.snapshot_date).all()
    
    # If no snapshots, create one for current state
    if not snapshots:
        current_snapshot = create_portfolio_snapshot(user_id, db)
        if current_snapshot:
            snapshots = [current_snapshot]
    
    # Prepare trend data
    trend_labels = []
    trend_values = []
    
    if interval == "monthly":
        # Group by month
        monthly_data = {}
        for snapshot in snapshots:
            month_key = snapshot.snapshot_date.strftime("%b %Y")  # e.g., "Jan 2026"
            if month_key not in monthly_data:
                monthly_data[month_key] = snapshot.total_investment_value
            else:
                # Use the latest snapshot for each month
                monthly_data[month_key] = snapshot.total_investment_value
        
        # Generate labels for last N months (even if no data)
        for i in range(months - 1, -1, -1):
            month_date = end_date - timedelta(days=i * 30)
            month_label = month_date.strftime("%b %Y")
            trend_labels.append(month_label)
            trend_values.append(monthly_data.get(month_label, 0.0))
    
    else:  # weekly
        # Group by week
        weekly_data = {}
        for snapshot in snapshots:
            week_key = snapshot.snapshot_date.strftime("%Y-W%U")
            week_label = snapshot.snapshot_date.strftime("%b %d")
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "label": week_label,
                    "value": snapshot.total_investment_value
                }
        
        # Sort by date and extract
        sorted_weeks = sorted(weekly_data.items())
        trend_labels = [item[1]["label"] for item in sorted_weeks]
        trend_values = [item[1]["value"] for item in sorted_weeks]
    
    # Calculate current totals
    current_investments = db.query(Investment).filter(Investment.user_id == user_id).all()
    total_current = sum(inv.current_value for inv in current_investments) if current_investments else 0.0
    total_initial = sum(inv.initial_value for inv in current_investments) if current_investments else 0.0
    total_growth = ((total_current - total_initial) / total_initial * 100) if total_initial > 0 else 0.0
    
    return {
        "total_current_value": total_current,
        "total_initial_value": total_initial,
        "total_growth_percentage": round(total_growth, 2),
        "trend_labels": trend_labels,
        "trend_values": trend_values,
        "interval": interval,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data_points": len(trend_values)
    }


def create_snapshots_for_all_investors(db: Session) -> int:
    """
    Create portfolio snapshots for all users with investments
    
    Used for periodic background tasks (e.g., monthly cron job)
    
    Returns:
        Number of snapshots created
    """
    from app.models.user import User
    
    # Get all users with investments
    users_with_investments = db.query(User.id).join(Investment).distinct().all()
    
    snapshots_created = 0
    for (user_id,) in users_with_investments:
        try:
            snapshot = create_portfolio_snapshot(user_id, db)
            if snapshot:
                snapshots_created += 1
        except Exception as e:
            logger.error(f"Error creating snapshot for user {user_id}: {e}")
            continue
    
    logger.info(f"Created {snapshots_created} portfolio snapshots")
    return snapshots_created
