from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_investor
from app.models.user import User
from app.models.investment import Investment
from app.models.property import Property
from app.schemas.investment import InvestmentResponse, InvestmentListResponse, InvestmentDetailResponse
from app.schemas.property import PropertyResponse

router = APIRouter(prefix="/api/investor", tags=["Investor"], dependencies=[Depends(require_investor)])


@router.get("/investments", response_model=InvestmentListResponse)
def get_my_investments(
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get all investments for the current investor
    
    Returns portfolio summary with growth calculations.
    """
    # Get all investments for this user
    investments = db.query(Investment).filter(Investment.user_id == current_user.id).all()
    
    # Enrich with property information
    investment_responses = []
    for investment in investments:
        property = db.query(Property).filter(Property.id == investment.property_id).first()
        
        inv_response = InvestmentResponse(
            id=investment.id,
            user_id=investment.user_id,
            property_id=investment.property_id,
            fractions_owned=investment.fractions_owned,
            ownership_percentage=investment.ownership_percentage,
            initial_value=investment.initial_value,
            current_value=investment.current_value,
            growth_percentage=investment.growth_percentage,
            growth_amount=investment.growth_amount,
            created_at=investment.created_at,
            updated_at=investment.updated_at,
            property_title=property.title if property else None,
            property_location=property.location if property else None
        )
        investment_responses.append(inv_response)
    
    # Calculate portfolio totals
    total_initial = sum(inv.initial_value for inv in investments)
    total_current = sum(inv.current_value for inv in investments)
    total_growth = ((total_current - total_initial) / total_initial * 100) if total_initial > 0 else 0
    
    return InvestmentListResponse(
        investments=investment_responses,
        total=len(investments),
        total_initial_value=total_initial,
        total_current_value=total_current,
        total_growth_percentage=total_growth
    )


@router.get("/investments/{investment_id}", response_model=InvestmentDetailResponse)
def get_investment_detail(
    investment_id: int,
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific investment
    
    Only returns investments owned by the current user.
    """
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )
    
    # Get full property details
    property = db.query(Property).filter(Property.id == investment.property_id).first()
    
    return InvestmentDetailResponse(
        id=investment.id,
        user_id=investment.user_id,
        property_id=investment.property_id,
        initial_value=investment.initial_value,
        current_value=investment.current_value,
        growth_percentage=investment.growth_percentage,
        growth_amount=investment.growth_amount,
        created_at=investment.created_at,
        updated_at=investment.updated_at,
        property=PropertyResponse.from_orm(property).model_dump() if property else {}
    )


@router.get("/portfolio/summary")
def get_portfolio_summary(
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get portfolio summary statistics for dashboard
    
    Returns:
        - Total investment value
        - Total fractions owned
        - Number of properties invested in
        - Average growth percentage
        - 6-month growth trend (for chart)
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Get all investments for this user
    investments = db.query(Investment).filter(Investment.user_id == current_user.id).all()
    
    if not investments:
        return {
            "total_investment": 0,
            "total_fractions": 0,
            "properties_count": 0,
            "active_investments": 0,
            "avg_growth": 0,
            "growth_trend": []
        }
    
    # Calculate totals
    total_current_value = sum(inv.current_value for inv in investments)
    total_fractions = sum(inv.fractions_owned or 0 for inv in investments)
    properties_count = len(set(inv.property_id for inv in investments))
    
    # Calculate average growth
    total_initial = sum(inv.initial_value for inv in investments)
    avg_growth = ((total_current_value - total_initial) / total_initial * 100) if total_initial > 0 else 0
    
    # Generate 6-month growth trend (simplified - using current values)
    # In production, you'd query historical data from a valuations table
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    base_value = total_initial
    monthly_growth = avg_growth / 6 if avg_growth > 0 else 0
    
    growth_trend = []
    current_value = base_value
    for i, month in enumerate(months):
        current_value += (base_value * monthly_growth / 100)
        growth_trend.append({
            "month": month,
            "value": round(current_value, 2)
        })
    
    return {
        "total_investment": round(total_current_value, 2),
        "total_fractions": total_fractions,
        "properties_count": properties_count,
        "active_investments": len(investments),
        "avg_growth": round(avg_growth, 2),
        "growth_trend": growth_trend
    }
