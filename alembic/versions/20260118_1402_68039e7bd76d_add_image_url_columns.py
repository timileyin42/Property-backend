from alembic import op
import sqlalchemy as sa


revision = "68039e7bd76d"
down_revision = "6c2cfc2fbe79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    investment_columns = [c["name"] for c in inspector.get_columns("investments")]
    if "image_url" not in investment_columns:
        op.add_column("investments", sa.Column("image_url", sa.String(), nullable=True))

    update_columns = [c["name"] for c in inspector.get_columns("updates")]
    if "image_url" not in update_columns:
        op.add_column("updates", sa.Column("image_url", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    update_columns = [c["name"] for c in inspector.get_columns("updates")]
    if "image_url" in update_columns:
        op.drop_column("updates", "image_url")

    investment_columns = [c["name"] for c in inspector.get_columns("investments")]
    if "image_url" in investment_columns:
        op.drop_column("investments", "image_url")
