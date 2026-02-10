"""Add international columns to schools table

Revision ID: 001_add_intl_columns
Revises: 
Create Date: 2026-02-09 09:47:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '001_add_intl_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """schools 테이블에 유학생 관련 컬럼 추가"""
    
    # 유학생 담당자 정보
    op.add_column('schools', sa.Column('international_email', sa.String(length=255), nullable=True))
    op.add_column('schools', sa.Column('international_phone', sa.String(length=50), nullable=True))
    
    # 취업률
    op.add_column('schools', sa.Column('employment_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    
    # JSONB 컬럼들
    op.add_column('schools', sa.Column('facilities', JSONB, nullable=True))
    op.add_column('schools', sa.Column('staff_info', JSONB, nullable=True))
    op.add_column('schools', sa.Column('esl_program', JSONB, nullable=True))
    op.add_column('schools', sa.Column('international_support', JSONB, nullable=True))
    
    # 인덱스 추가 (검색 성능 향상)
    op.create_index('idx_schools_international_email', 'schools', ['international_email'], unique=False)


def downgrade() -> None:
    """변경 사항 롤백"""
    
    # 인덱스 삭제
    op.drop_index('idx_schools_international_email', table_name='schools')
    
    # 컬럼 삭제
    op.drop_column('schools', 'international_support')
    op.drop_column('schools', 'esl_program')
    op.drop_column('schools', 'staff_info')
    op.drop_column('schools', 'facilities')
    op.drop_column('schools', 'employment_rate')
    op.drop_column('schools', 'international_phone')
    op.drop_column('schools', 'international_email')
