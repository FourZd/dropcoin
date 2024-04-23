"""alter twitter post id

Revision ID: ba95fec0eda3
Revises: b01b0bd59b6d
Create Date: 2024-04-23 22:06:00.604962

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba95fec0eda3'
down_revision = 'b01b0bd59b6d'
branch_labels = None
depends_on = None


def upgrade():
    # Use the batch_alter_table context manager to group operations
    with op.batch_alter_table('twitter_posts', schema=None) as batch_op:
        # Add a new temporary integer column
        batch_op.add_column(sa.Column('new_id', sa.Integer(), autoincrement=True))

        # Make sure to commit the transaction that adds the column
        batch_op.execute('COMMIT;')

        # Update the new_id column by casting the old id values to integers
        batch_op.execute('UPDATE twitter_posts SET new_id = CAST(id AS INTEGER);')

        # Drop the old 'id' column
        batch_op.drop_column('id')

        # Rename the new column to 'id'
        batch_op.alter_column('new_id', new_column_name='id')

def downgrade():
    # Reversing the upgrade steps
    with op.batch_alter_table('twitter_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('old_id', sa.VARCHAR()))
        batch_op.execute('COMMIT;')
        # Copy data back from 'id' to 'old_id'
        batch_op.execute('UPDATE twitter_posts SET old_id = CAST(id AS VARCHAR)')

        # Drop the current 'id' column
        batch_op.drop_column('id')

        # Rename 'old_id' back to 'id'
        batch_op.alter_column('old_id', new_column_name='id')