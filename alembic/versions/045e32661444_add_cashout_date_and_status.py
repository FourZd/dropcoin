"""add cashout date and status

Revision ID: 045e32661444
Revises: 6b1b9f691d95
Create Date: 2024-04-20 20:17:37.197947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '045e32661444'
down_revision = '6b1b9f691d95'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE TYPE result_types AS ENUM ('win', 'lose', 'pending')")
    op.add_column('crash_bets', sa.Column('cash_out_datetime', sa.DateTime(timezone=True), nullable=True))
    op.add_column('crash_bets', sa.Column('result', sa.Enum('win', 'lose', 'pending', name='result_types'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('crash_bets', 'result')
    op.drop_column('crash_bets', 'cash_out_datetime')
    op.execute("DROP TYPE result_types")
    # ### end Alembic commands ###
