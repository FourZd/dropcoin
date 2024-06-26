"""update for microservices

Revision ID: 4ef16a09f8fb
Revises: 013c7e48912f
Create Date: 2024-05-15 16:13:49.859857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ef16a09f8fb'
down_revision = '013c7e48912f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    op.add_column('crash_bets', sa.Column('hash', sa.String(), nullable=True))
    op.drop_constraint('crash_bets_game_id_fkey', 'crash_bets', type_='foreignkey')
    op.drop_column('crash_bets', 'game_id')
    op.add_column('game_state', sa.Column('current_game_hash', sa.String(), nullable=True))
    op.add_column('game_state', sa.Column('current_result', sa.Numeric(), nullable=True))
    op.add_column('game_state', sa.Column('last_game_hash', sa.String(), nullable=True))
    op.alter_column('game_state', 'last_game_result',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(),
               existing_nullable=True)
    op.drop_constraint('game_state_current_game_hash_id_fkey', 'game_state', type_='foreignkey')
    op.drop_constraint('game_state_last_game_hash_id_fkey', 'game_state', type_='foreignkey')
    op.drop_column('game_state', 'current_game_hash_id')
    op.drop_column('game_state', 'last_game_hash_id')
    op.drop_table('crash_hashes')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game_state', sa.Column('last_game_hash_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('game_state', sa.Column('current_game_hash_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('game_state_last_game_hash_id_fkey', 'game_state', 'crash_hashes', ['last_game_hash_id'], ['id'])
    op.create_foreign_key('game_state_current_game_hash_id_fkey', 'game_state', 'crash_hashes', ['current_game_hash_id'], ['id'])
    op.alter_column('game_state', 'last_game_result',
               existing_type=sa.Numeric(),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.drop_column('game_state', 'last_game_hash')
    op.drop_column('game_state', 'current_result')
    op.drop_column('game_state', 'current_game_hash')
    op.add_column('crash_bets', sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('crash_bets_game_id_fkey', 'crash_bets', 'crash_hashes', ['game_id'], ['id'])
    op.drop_column('crash_bets', 'hash')
    op.create_table('crash_hashes',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('hash', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='crash_hashes_pkey')
    )
    # ### end Alembic commands ###
