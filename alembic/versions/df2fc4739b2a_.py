"""empty message

Revision ID: df2fc4739b2a
Revises: 4cdc6dc68159
Create Date: 2024-05-26 16:35:12.720135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df2fc4739b2a'
down_revision = '4cdc6dc68159'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))


def downgrade():
    op.drop_column('user_rewards', 'email')
