"""make usernmae unnecesary field

Revision ID: 4cdc6dc68159
Revises: e7e880f57eff
Create Date: 2024-05-16 21:43:12.598153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cdc6dc68159'
down_revision = 'e7e880f57eff'
branch_labels = None
depends_on = None


def upgrade():
    # Инструкции для миграции вверх (добавление nullable)
    op.alter_column('users', 'username',
                    existing_type=sa.String(),
                    nullable=True)

def downgrade():
    # Инструкции для миграции вниз (удаление nullable)
    op.alter_column('users', 'username',
                    existing_type=sa.String(),
                    nullable=False)