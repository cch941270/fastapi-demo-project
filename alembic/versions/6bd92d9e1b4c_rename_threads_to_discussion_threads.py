"""rename threads to discussion_threads

Revision ID: 6bd92d9e1b4c
Revises: 10a141ac9809
Create Date: 2025-12-22 23:24:31.372837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd92d9e1b4c'
down_revision: Union[str, Sequence[str], None] = '10a141ac9809'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("threads", "discussion_threads")
    op.execute("ALTER SEQUENCE threads_id_seq RENAME TO discussion_threads_id_seq")
    op.execute("ALTER INDEX threads_pkey RENAME TO discussion_threads_pkey")
    op.execute("ALTER INDEX ix_threads_title RENAME TO ix_discussion_threads_title")
    op.execute("ALTER INDEX ix_threads_user_id RENAME TO ix_discussion_threads_user_id")
    op.execute("ALTER TABLE discussion_threads RENAME CONSTRAINT threads_user_id_fkey TO discussion_threads_user_id_fkey")


def downgrade() -> None:
    op.rename_table("discussion_threads", "threads")
    op.execute("ALTER SEQUENCE discussion_threads_id_seq RENAME TO threads_id_seq")
    op.execute("ALTER INDEX discussion_threads_pkey RENAME TO threads_pkey")
    op.execute("ALTER INDEX ix_discussion_threads_title RENAME TO ix_threads_title")
    op.execute("ALTER INDEX ix_discussion_threads_user_id RENAME TO ix_threads_user_id")
    op.execute("ALTER TABLE threads RENAME CONSTRAINT discussion_threads_user_id_fkey TO threads_user_id_fkey")
