"""
SQLAlchemy 데이터베이스 모델
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from .connection import Base


class School(Base):
    """학교 정보 모델"""
    __tablename__ = 'schools'
    
    # 기존 컬럼
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    state = Column(String(100))
    city = Column(String(100))
    tuition = Column(Integer)
    living_cost = Column(Integer)
    ranking = Column(Integer)
    description = Column(Text)
    acceptance_rate = Column(Integer)
    transfer_rate = Column(Integer)
    graduation_rate = Column(Integer)
    website = Column(String(500))
    global_ranking = Column(String(50))
    ranking_field = Column(String(255))
    average_salary = Column(Integer)
    alumni_network_count = Column(Integer)
    feature_badges = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 추가할 컬럼 (마이그레이션으로 추가 예정)
    international_email = Column(String(255))
    international_phone = Column(String(50))
    employment_rate = Column(Numeric(5, 2))
    facilities = Column(JSONB)  # 시설 정보
    staff_info = Column(JSONB)  # 스텝 현황
    esl_program = Column(JSONB)  # ESL 프로그램
    international_support = Column(JSONB)  # 유학생 지원
    
    # Relationships
    programs = relationship("Program", back_populates="school")
    school_documents = relationship("SchoolDocument", back_populates="school")
    
    def __repr__(self):
        return f"<School(id={self.id}, name='{self.name}', state='{self.state}')>"


class Program(Base):
    """프로그램 정보 모델"""
    __tablename__ = 'programs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    degree = Column(String(50))
    duration = Column(String(100))
    tuition = Column(Integer)
    description = Column(Text)
    requirements = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    school = relationship("School", back_populates="programs")
    
    def __repr__(self):
        return f"<Program(id={self.id}, name='{self.name}', type='{self.type}')>"


class SchoolDocument(Base):
    """학교 문서 모델 (긴 텍스트 저장용)"""
    __tablename__ = 'school_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id', ondelete='CASCADE'), nullable=False)
    document_type = Column(String(50), nullable=False)  # 'history', 'environment', 'detailed_info'
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    doc_metadata = Column('metadata', JSONB)  # 'metadata'는 SQLAlchemy 예약어이므로 컬럼명 매핑
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    school = relationship("School", back_populates="school_documents")
    
    def __repr__(self):
        return f"<SchoolDocument(id={self.id}, type='{self.document_type}', title='{self.title}')>"


class AuditLog(Base):
    """감사 로그 모델"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(255), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(255), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE', 'CRAWL'
    actor_id = Column(UUID(as_uuid=True))  # FK to users removed for local dev
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    after_data = Column(Text)
    before_data = Column(Text)
    ip_address = Column(String(255))
    user_id = Column(UUID(as_uuid=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))  # FK to users removed for local dev
    updated_by = Column(UUID(as_uuid=True))  # FK to users removed for local dev
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', action='{self.action}')>"
