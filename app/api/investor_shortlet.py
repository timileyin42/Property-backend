from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_investor
from app.models.user import User
from app.models.investment import Investment
from app.models.occupancy import PropertyOccupancy
from app.models.revenue import PropertyRevenue
from app.models.distribution import EarningsDistribution, DistributionStatus
from app.schemas.occupancy import OccupancyResponse
from app.schemas.revenue import RevenueResponse
from app.schemas.distribution import DistributionResponse, InvestorEarningsSummary
from app.services.distribution_service import get_investor_earnings_summary

router = APIRouter(prefix="/api/investor/shortlet", tags=["Investor - Shortlet Data"], dependencies=[Depends(require_investor)])


@router.get("/investments/{investment_id}/occupancy", response_model=list[OccupancyResponse])
def get_investment_occupancy(
    investment_id: int,
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get occupancy data for an investment property (Investor only)
    """
    # Verify investment belongs to current user
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )
    
    # Get occupancy records for the property
    occupancy_records = db.query(PropertyOccupancy).filter(
        PropertyOccupancy.property_id == investment.property_id
    ).order_by(PropertyOccupancy.year.desc(), PropertyOccupancy.month.desc()).all()
    
    return occupancy_records


@router.get("/investments/{investment_id}/revenue", response_model=list[RevenueResponse])
def get_investment_revenue(
    investment_id: int,
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get revenue data for an investment property (Investor only)
    """
    # Verify investment belongs to current user
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )
    
    # Get revenue records for the property
    revenue_records = db.query(PropertyRevenue).filter(
        PropertyRevenue.property_id == investment.property_id
    ).order_by(PropertyRevenue.year.desc(), PropertyRevenue.month.desc()).all()
    
    return revenue_records


@router.get("/earnings", response_model=list[DistributionResponse])
def get_my_earnings(
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get all earnings distributions for current investor
    """
    # Get all distributions for this investor's investments
    distributions = db.query(EarningsDistribution).join(
        Investment
    ).filter(
        Investment.user_id == current_user.id
    ).order_by(EarningsDistribution.created_at.desc()).all()
    
    # Enrich with property info
    for dist in distributions:
        if dist.investment and dist.investment.investment_property:
            dist.property_title = dist.investment.investment_property.title
        if dist.revenue:
            dist.period_label = dist.revenue.period_label
    
    return distributions


@router.get("/earnings/summary", response_model=InvestorEarningsSummary)
def get_earnings_summary(
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get earnings summary for current investor
    """
    summary = get_investor_earnings_summary(current_user.id, db)
    return InvestorEarningsSummary(**summary)
