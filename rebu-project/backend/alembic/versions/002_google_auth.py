from alembic import op
import sqlalchemy as sa

revision = "002_google_auth"
down_revision = "001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("auth_provider", sa.String(), nullable=False, server_default="local"))
    op.add_column("users", sa.Column("google_sub", sa.String(), nullable=True))

    op.alter_column("users", "phone", existing_type=sa.String(), nullable=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=True)

    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])

def downgrade():
    op.drop_constraint("uq_users_google_sub", "users", type_="unique")
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "phone", existing_type=sa.String(), nullable=False)
    op.drop_column("users", "google_sub")
    op.drop_column("users", "auth_provider")