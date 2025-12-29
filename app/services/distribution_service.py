"""
Service for calculating and managing earnings distributions
"""

from sqlalchemy.orm import Session
from app.models.revenue import PropertyRevenue
from app.models.investment import Investment
from app.models.distribution import EarningsDistribution, DistributionStatus
from app.models.property import Property
from typing import List
from datetime import datetime


def calculate_and_create_distributions(
    revenue_id: int,
    db: Session
) -> List[EarningsDistribution]:
    """
    Calculate earnings for all investors and create distribution records
    
    Args:
        revenue_id: ID of the revenue record to distribute
        db: Database session
    
    Returns:
        List of created distribution records
    
    Raises:
        ValueError: If revenue not found or already distributed
    """
    # Get revenue record
    revenue = db.query(PropertyRevenue).filter(PropertyRevenue.id == revenue_id).first()
    if not revenue:
        raise ValueError("Revenue record not found")
    
    if revenue.distributed:
        raise ValueError("Revenue already distributed")
    
    # Get property
    property = db.query(Property).filter(Property.id == revenue.property_id).first()
    if not property:
        raise ValueError("Property not found")
    
    # Check if property is fractional
    if not property.is_fractional:
        raise ValueError("Property does not use fractional ownership")
    
    # Get all investments for this property
    investments = db.query(Investment).filter(
        Investment.property_id == revenue.property_id
    ).all()
    
    if not investments:
        raise ValueError("No investments found for this property")
    
    # Calculate net income
    net_income = revenue.net_income
    
    if net_income <= 0:
        raise ValueError("Net income must be positive to distribute")
    
    # Create distribution records
    distributions = []
    
    for investment in investments:
        if not investment.fractions_owned:
            continue  # Skip non-fractional investments
        
        # Calculate ownership percentage
        ownership_pct = (investment.fractions_owned / property.total_fractions) * 100
        
        # Calculate earnings amount
        earnings = (investment.fractions_owned / property.total_fractions) * net_income
        
        # Create distribution record
        distribution = EarningsDistribution(
            property_revenue_id=revenue_id,
            investment_id=investment.id,
            fractions_owned=investment.fractions_owned,
            ownership_percentage=ownership_pct,
            earnings_amount=earnings,
            status=DistributionStatus.PENDING
        )
        
        db.add(distribution)
        distributions.append(distribution)
    
    # Mark revenue as distributed
    revenue.distributed = True
    revenue.distribution_date = datetime.utcnow()
    
    db.commit()
    
    # Refresh all distributions
    for dist in distributions:
        db.refresh(dist)
    
    return distributions


def get_investor_earnings_summary(user_id: int, db: Session) -> dict:
    """
    Get earnings summary for an investor
    
    Args:
        user_id: ID of the investor
        db: Database session
    
    Returns:
        Dictionary with earnings summary
    """
    # Get all distributions for this investor
    distributions = db.query(EarningsDistribution).join(
        Investment
    ).filter(
        Investment.user_id == user_id
    ).all()
    
    total_earnings = sum(d.earnings_amount for d in distributions)
    total_paid = sum(d.earnings_amount for d in distributions if d.status == DistributionStatus.PAID)
    total_pending = sum(d.earnings_amount for d in distributions if d.status == DistributionStatus.PENDING)
    
    # Count unique properties
    property_ids = set(d.investment.property_id for d in distributions)
    
    return {
        "total_earnings": total_earnings,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "distributions_count": len(distributions),
        "properties_count": len(property_ids)
    }
