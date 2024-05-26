"""empty message

Revision ID: 0d0370295dd8
Revises: df2fc4739b2a
Create Date: 2024-05-26 16:46:37.979232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d0370295dd8'
down_revision = 'df2fc4739b2a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('available_rewards', sa.Column('tag', sa.String(), nullable=True))


def downgrade():
    op.drop_column('available_rewards', 'tag')