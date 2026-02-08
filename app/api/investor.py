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
    
    # Aggregate investments by property (single card per property)
    aggregated = {}
    for investment in investments:
        property = db.query(Property).filter(Property.id == investment.property_id).first()
        if investment.property_id not in aggregated:
            aggregated[investment.property_id] = {
                "investment_ids": [investment.id],
                "user_id": investment.user_id,
                "property": property,
                "fractions_owned": investment.fractions_owned or 0,
                "initial_value": investment.initial_value,
                "current_value": investment.current_value,
                "created_at": investment.created_at,
                "updated_at": investment.updated_at,
            }
        else:
            agg = aggregated[investment.property_id]
            agg["investment_ids"].append(investment.id)
            agg["fractions_owned"] += investment.fractions_owned or 0
            agg["initial_value"] += investment.initial_value
            agg["current_value"] += investment.current_value
            if investment.created_at < agg["created_at"]:
                agg["created_at"] = investment.created_at
            if investment.updated_at > agg["updated_at"]:
                agg["updated_at"] = investment.updated_at
    
    # Build response list (one entry per property)
    investment_responses = []
    for property_id, agg in aggregated.items():
        property = agg["property"]
        total_initial = agg["initial_value"]
        total_current = agg["current_value"]
        growth_amount = total_current - total_initial
        growth_percentage = (growth_amount / total_initial * 100) if total_initial > 0 else 0.0
        
        ownership_percentage = 0.0
        if property and property.total_fractions:
            ownership_percentage = (agg["fractions_owned"] / property.total_fractions) * 100
        
        inv_response = InvestmentResponse(
            id=min(agg["investment_ids"]),
            user_id=agg["user_id"],
            property_id=property_id,
            fractions_owned=agg["fractions_owned"],
            fractions_sold=property.fractions_sold if property else None,
            ownership_percentage=ownership_percentage,
            initial_value=total_initial,
            current_value=total_current,
            growth_percentage=growth_percentage,
            growth_amount=growth_amount,
            created_at=agg["created_at"],
            updated_at=agg["updated_at"],
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
        total=len(investment_responses),
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
    Get portfolio summary statistics for dashboard with real trend data
    
    Returns:
        - Total investment value
        - Total fractions owned
        - Number of properties invested in
        - Average growth percentage
        - Historical growth trend (from snapshots)
    """
    from app.services.portfolio_service import get_portfolio_trend, create_portfolio_snapshot
    
    # Get all investments for this user
    investments = db.query(Investment).filter(Investment.user_id == current_user.id).all()
    
    if not investments:
        return {
            "total_investment": 0,
            "total_fractions": 0,
            "properties_count": 0,
            "active_investments": 0,
            "avg_growth": 0,
            "trend_labels": [],
            "trend_values": []
        }
    
    # Calculate current totals
    total_current_value = sum(inv.current_value for inv in investments)
    total_initial_value = sum(inv.initial_value for inv in investments)
    total_fractions = sum(inv.fractions_owned or 0 for inv in investments)
    properties_count = len(set(inv.property_id for inv in investments))
    avg_growth = ((total_current_value - total_initial_value) / total_initial_value * 100) if total_initial_value > 0 else 0
    
    # Ensure current snapshot exists
    create_portfolio_snapshot(current_user.id, db)
    
    # Get trend data (6 months monthly by default)
    trend_data = get_portfolio_trend(current_user.id, db, interval="monthly", months=6)
    
    return {
        "total_investment": round(total_current_value, 2),
        "total_initial_value": round(total_initial_value, 2),
        "total_fractions": total_fractions,
        "properties_count": properties_count,
        "active_investments": len(investments),
        "avg_growth": round(avg_growth, 2),
        "trend_labels": trend_data["trend_labels"],
        "trend_values": trend_data["trend_values"],
        "interval": trend_data["interval"],
        "data_points": trend_data["data_points"]
    }


@router.get("/portfolio/trend")
def get_portfolio_trend_endpoint(
    interval: str = "monthly",
    months: int = 6,
    current_user: User = Depends(require_investor),
    db: Session = Depends(get_db)
):
    """
    Get portfolio value trend over time for charting
    
    Query params:
        interval: "monthly" or "weekly" (default: monthly)
        months: Number of months to look back (default: 6)
    
    Returns trend data with labels and values for charts
    """
    from app.services.portfolio_service import get_portfolio_trend, create_portfolio_snapshot
    
    # Validate interval
    if interval not in ["monthly", "weekly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interval. Use 'monthly' or 'weekly'"
        )
    
    # Validate months
    if months < 1 or months > 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Months must be between 1 and 24"
        )
    
    # Ensure current snapshot exists
    create_portfolio_snapshot(current_user.id, db)
    
    # Get trend data
    return get_portfolio_trend(current_user.id, db, interval=interval, months=months)
