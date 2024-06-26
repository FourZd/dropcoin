"""remove twitter parameters

Revision ID: e9299f14f44c
Revises: f77ed6e25140
Create Date: 2024-05-09 23:45:51.344290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9299f14f44c'
down_revision = 'f77ed6e25140'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'access_token')
    op.drop_column('users', 'telegram')
    op.drop_column('users', 'access_token_secret')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('access_token_secret', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('telegram', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('access_token', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
