"""Add crawl metadata columns to schools table (hybrid design)

Revision ID: 003_add_school_crawl_metadata
Revises: 002_remove_embedding
Create Date: 2026-02-11 09:00:00

하이브리드 설계:
- schools 테이블에 "최신 크롤링 상태"를 저장하여 모니터/대시보드 조회를 안정화
- audit_logs는 append-only 히스토리로 유지 (선택/보조 지표)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_add_school_crawl_metadata"
down_revision = "002_remove_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("last_crawled_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("schools", sa.Column("last_crawl_status", sa.String(length=20), nullable=True))
    op.add_column("schools", sa.Column("last_crawl_message", sa.Text(), nullable=True))
    op.add_column("schools", sa.Column("last_crawl_data_updated_at", sa.TIMESTAMP(timezone=True), nullable=True))

    op.create_index("idx_schools_last_crawled_at", "schools", ["last_crawled_at"], unique=False)
    op.create_index("idx_schools_last_crawl_status", "schools", ["last_crawl_status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_schools_last_crawl_status", table_name="schools")
    op.drop_index("idx_schools_last_crawled_at", table_name="schools")

    op.drop_column("schools", "last_crawl_data_updated_at")
    op.drop_column("schools", "last_crawl_message")
    op.drop_column("schools", "last_crawl_status")
    op.drop_column("schools", "last_crawled_at")

