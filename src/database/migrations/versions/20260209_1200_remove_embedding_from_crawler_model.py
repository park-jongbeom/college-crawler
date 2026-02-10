"""Remove embedding from college-crawler SchoolDocument model (documentation)

Revision ID: 002_remove_embedding
Revises: 001_add_intl_columns
Create Date: 2026-02-09 12:00:00

college-crawler는 웹 크롤링만 담당하며 임베딩을 생성하지 않음.
school_documents.embedding 컬럼의 NOT NULL 해제는 ga-api-platform Flyway V8에서 수행.
이 마이그레이션은 모델에서 embedding 필드 제거에 대한 기록용이며, DB 스키마 변경 없음.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '002_remove_embedding'
down_revision = '001_add_intl_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DB 스키마 변경 없음. embedding nullable 변경은 ga-api-platform V8 마이그레이션에서 처리.
    pass


def downgrade() -> None:
    pass
