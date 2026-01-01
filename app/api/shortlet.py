from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.user import User
from app.models.property import Property
from app.models.occupancy import PropertyOccupancy
from app.models.revenue import PropertyRevenue
from app.models.distribution import EarningsDistribution, DistributionStatus
from app.schemas.occupancy import (
    OccupancyCreate,
    OccupancyUpdate,
    OccupancyResponse,
    OccupancyListResponse
)
from app.schemas.revenue import (
    RevenueCreate,
    RevenueUpdate,
    RevenueResponse,
    RevenueListResponse,
    DistributeRevenueRequest
)
from app.schemas.distribution import (
    DistributionResponse,
    DistributionStatusUpdate,
    DistributionListResponse
)
from app.services.distribution_service import calculate_and_create_distributions

router = APIRouter(prefix="/api/admin/shortlet", tags=["Admin - Shortlet Management"], dependencies=[Depends(require_admin)])



@router.post("/occupancy", response_model=OccupancyResponse, status_code=status.HTTP_201_CREATED)
def create_occupancy_record(
    occupancy_data: OccupancyCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Record occupancy data for a property (Admin only)
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == occupancy_data.property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check for duplicate period
    existing = db.query(PropertyOccupancy).filter(
        PropertyOccupancy.property_id == occupancy_data.property_id,
        PropertyOccupancy.month == occupancy_data.month,
        PropertyOccupancy.year == occupancy_data.year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Occupancy record already exists for {occupancy_data.month}/{occupancy_data.year}"
        )
    
    # Create occupancy record
    occupancy = PropertyOccupancy(
        **occupancy_data.model_dump(),
        created_by=current_user.id
    )
    
    db.add(occupancy)
    db.commit()
    db.refresh(occupancy)
    
    return occupancy


@router.get("/properties/{property_id}/occupancy", response_model=OccupancyListResponse)
def get_property_occupancy(
    property_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get occupancy history for a property (Admin only)
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Get occupancy records
    records = db.query(PropertyOccupancy).filter(
        PropertyOccupancy.property_id == property_id
    ).order_by(PropertyOccupancy.year.desc(), PropertyOccupancy.month.desc()).all()
    
    # Calculate average occupancy rate
    avg_rate = 0.0
    if records:
        avg_rate = sum(r.occupancy_rate for r in records) / len(records)
    
    return OccupancyListResponse(
        occupancy_records=records,
        total=len(records),
        average_occupancy_rate=avg_rate
    )


@router.patch("/occupancy/{occupancy_id}", response_model=OccupancyResponse)
def update_occupancy_record(
    occupancy_id: int,
    occupancy_data: OccupancyUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update occupancy record (Admin only)
    """
    occupancy = db.query(PropertyOccupancy).filter(PropertyOccupancy.id == occupancy_id).first()
    if not occupancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Occupancy record not found"
        )
    
    # Update fields
    update_data = occupancy_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(occupancy, field, value)
    
    db.commit()
    db.refresh(occupancy)
    
    return occupancy



@router.post("/revenue", response_model=RevenueResponse, status_code=status.HTTP_201_CREATED)
def create_revenue_record(
    revenue_data: RevenueCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Record revenue data for a property (Admin only)
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == revenue_data.property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check for duplicate period
    existing = db.query(PropertyRevenue).filter(
        PropertyRevenue.property_id == revenue_data.property_id,
        PropertyRevenue.month == revenue_data.month,
        PropertyRevenue.year == revenue_data.year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Revenue record already exists for {revenue_data.month}/{revenue_data.year}"
        )
    
    # Create revenue record
    revenue = PropertyRevenue(
        **revenue_data.model_dump(),
        created_by=current_user.id
    )
    
    db.add(revenue)
    db.commit()
    db.refresh(revenue)
    
    return revenue


@router.get("/properties/{property_id}/revenue", response_model=RevenueListResponse)
def get_property_revenue(
    property_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get revenue history for a property (Admin only)
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Get revenue records
    records = db.query(PropertyRevenue).filter(
        PropertyRevenue.property_id == property_id
    ).order_by(PropertyRevenue.year.desc(), PropertyRevenue.month.desc()).all()
    
    # Calculate totals
    total_gross = sum(r.gross_revenue for r in records)
    total_expenses = sum(r.expenses for r in records)
    total_net = sum(r.net_income for r in records)
    
    return RevenueListResponse(
        revenue_records=records,
        total=len(records),
        total_gross_revenue=total_gross,
        total_expenses=total_expenses,
        total_net_income=total_net
    )


@router.patch("/revenue/{revenue_id}", response_model=RevenueResponse)
def update_revenue_record(
    revenue_id: int,
    revenue_data: RevenueUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update revenue record (Admin only)
    """
    revenue = db.query(PropertyRevenue).filter(PropertyRevenue.id == revenue_id).first()
    if not revenue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revenue record not found"
        )
    
    if revenue.distributed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update revenue that has already been distributed"
        )
    
    # Update fields
    update_data = revenue_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(revenue, field, value)
    
    db.commit()
    db.refresh(revenue)
    
    return revenue


@router.post("/revenue/{revenue_id}/distribute", response_model=dict)
def distribute_revenue(
    revenue_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Calculate and create earnings distributions for a revenue period (Admin only)
    """
    try:
        distributions = calculate_and_create_distributions(revenue_id, db)
        
        return {
            "success": True,
            "message": f"Created {len(distributions)} distribution records",
            "distributions_count": len(distributions),
            "total_distributed": sum(d.earnings_amount for d in distributions)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.get("/distributions", response_model=DistributionListResponse)
def get_all_distributions(
    property_id: int = Query(None),
    status_filter: DistributionStatus = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all earnings distributions (Admin only)
    """
    query = db.query(EarningsDistribution)
    
    # Filter by property if specified
    if property_id:
        query = query.join(PropertyRevenue).filter(PropertyRevenue.property_id == property_id)
    
    # Filter by status if specified
    if status_filter:
        query = query.filter(EarningsDistribution.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Get distributions
    distributions = query.order_by(EarningsDistribution.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with property info
    for dist in distributions:
        if dist.investment and dist.investment.property:
            dist.property_title = dist.investment.property.title
        if dist.revenue:
            dist.period_label = dist.revenue.period_label
    
    # Calculate totals
    total_earnings = sum(d.earnings_amount for d in distributions)
    total_paid = sum(d.earnings_amount for d in distributions if d.status == DistributionStatus.PAID)
    total_pending = sum(d.earnings_amount for d in distributions if d.status == DistributionStatus.PENDING)
    
    return DistributionListResponse(
        distributions=distributions,
        total=total,
        total_earnings=total_earnings,
        total_paid=total_paid,
        total_pending=total_pending
    )


@router.patch("/distributions/{distribution_id}/status", response_model=DistributionResponse)
def update_distribution_status(
    distribution_id: int,
    status_update: DistributionStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update distribution payment status (Admin only)
    """
    distribution = db.query(EarningsDistribution).filter(EarningsDistribution.id == distribution_id).first()
    if not distribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distribution not found"
        )
    
    # Update status
    distribution.status = status_update.status
    
    if status_update.status == DistributionStatus.PAID:
        from datetime import datetime
        distribution.paid_date = datetime.utcnow()
    
    if status_update.payment_reference:
        distribution.payment_reference = status_update.payment_reference
    
    if status_update.notes:
        distribution.notes = status_update.notes
    
    db.commit()
    db.refresh(distribution)
    
    return distribution
