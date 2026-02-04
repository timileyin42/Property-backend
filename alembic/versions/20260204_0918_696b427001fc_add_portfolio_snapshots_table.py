"""add portfolio snapshots table

Revision ID: 696b427001fc
Revises: d4e5f6a7b8c9
Create Date: 2026-02-04 09:18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '696b427001fc'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_investment_value', sa.Float(), nullable=False),
        sa.Column('total_initial_value', sa.Float(), nullable=False),
        sa.Column('total_earnings_received', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('growth_percentage', sa.Float(), nullable=False),
        sa.Column('growth_amount', sa.Float(), nullable=False),
        sa.Column('active_investments_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_portfolio_snapshots_user_id', 'portfolio_snapshots', ['user_id'])
    op.create_index('ix_portfolio_snapshots_snapshot_date', 'portfolio_snapshots', ['snapshot_date'])
    op.create_index('ix_portfolio_snapshots_user_date', 'portfolio_snapshots', ['user_id', 'snapshot_date'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_portfolio_snapshots_user_date', 'portfolio_snapshots')
    op.drop_index('ix_portfolio_snapshots_snapshot_date', 'portfolio_snapshots')
    op.drop_index('ix_portfolio_snapshots_user_id', 'portfolio_snapshots')
    op.drop_table('portfolio_snapshots')
