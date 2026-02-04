from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PortfolioSnapshot(Base):
    """
    Historical snapshot of a user's portfolio value at a specific date
    
    Created automatically when:
    - Admin updates investment values
    - Admin distributes earnings
    - Periodic monthly snapshots (background task)
    """
    
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Snapshot date (only date, not time - one snapshot per day max)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Aggregated portfolio values at this date
    total_investment_value = Column(Float, nullable=False)  # Sum of all current_values
    total_initial_value = Column(Float, nullable=False)     # Sum of all initial_values
    total_earnings_received = Column(Float, default=0.0)    # Cumulative earnings to date
    
    # Growth metrics
    growth_percentage = Column(Float, nullable=False)       # Calculated growth %
    growth_amount = Column(Float, nullable=False)           # Absolute growth
    
    # Number of active investments at this date
    active_investments_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<PortfolioSnapshot(user_id={self.user_id}, date={self.snapshot_date}, value={self.total_investment_value})>"
