"""
데이터베이스 Repository 패턴 구현
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID

from .models import School, Program, SchoolDocument, AuditLog
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SchoolRepository:
    """학교 정보 CRUD 작업"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, school_data: dict) -> School:
        """
        새로운 학교 생성
        
        Args:
            school_data: 학교 정보 딕셔너리
            
        Returns:
            생성된 School 객체
        """
        try:
            school = School(**school_data)
            self.db.add(school)
            self.db.flush()
            logger.info(f"학교 생성 완료: {school.name} ({school.id})")
            return school
        except Exception as e:
            logger.error(f"학교 생성 실패: {e}")
            raise
    
    def get_by_id(self, school_id: UUID) -> Optional[School]:
        """
        ID로 학교 조회
        
        Args:
            school_id: 학교 UUID
            
        Returns:
            School 객체 또는 None
        """
        return self.db.query(School).filter(School.id == school_id).first()
    
    def get_by_name(self, name: str, state: Optional[str] = None) -> Optional[School]:
        """
        이름으로 학교 조회
        
        Args:
            name: 학교 이름
            state: 주 이름 (선택)
            
        Returns:
            School 객체 또는 None
        """
        query = self.db.query(School).filter(School.name == name)
        if state:
            query = query.filter(School.state == state)
        return query.first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[School]:
        """
        모든 학교 조회
        
        Args:
            skip: 건너뛸 개수
            limit: 최대 조회 개수
            
        Returns:
            School 객체 리스트
        """
        return self.db.query(School).offset(skip).limit(limit).all()
    
    def get_by_state(self, state: str) -> List[School]:
        """
        주별 학교 조회
        
        Args:
            state: 주 이름 (CA, TX 등)
            
        Returns:
            School 객체 리스트
        """
        return self.db.query(School).filter(School.state == state).all()
    
    def get_by_type(self, school_type: str) -> List[School]:
        """
        유형별 학교 조회
        
        Args:
            school_type: 학교 유형 (Community College 등)
            
        Returns:
            School 객체 리스트
        """
        return self.db.query(School).filter(School.type == school_type).all()
    
    def update(self, school_id: UUID, update_data: dict) -> Optional[School]:
        """
        학교 정보 업데이트
        
        Args:
            school_id: 학교 UUID
            update_data: 업데이트할 데이터 딕셔너리
            
        Returns:
            업데이트된 School 객체 또는 None
        """
        try:
            school = self.get_by_id(school_id)
            if not school:
                logger.warning(f"학교를 찾을 수 없음: {school_id}")
                return None
            
            for key, value in update_data.items():
                if hasattr(school, key):
                    setattr(school, key, value)
            
            self.db.flush()
            logger.info(f"학교 업데이트 완료: {school.name} ({school_id})")
            return school
        except Exception as e:
            logger.error(f"학교 업데이트 실패: {e}")
            raise
    
    def delete(self, school_id: UUID) -> bool:
        """
        학교 삭제
        
        Args:
            school_id: 학교 UUID
            
        Returns:
            삭제 성공 여부
        """
        try:
            school = self.get_by_id(school_id)
            if not school:
                logger.warning(f"학교를 찾을 수 없음: {school_id}")
                return False
            
            self.db.delete(school)
            self.db.flush()
            logger.info(f"학교 삭제 완료: {school.name} ({school_id})")
            return True
        except Exception as e:
            logger.error(f"학교 삭제 실패: {e}")
            raise
    
    def exists(self, name: str, state: Optional[str] = None) -> bool:
        """
        학교 존재 여부 확인
        
        Args:
            name: 학교 이름
            state: 주 이름 (선택)
            
        Returns:
            존재 여부
        """
        return self.get_by_name(name, state) is not None
    
    def count(self) -> int:
        """
        전체 학교 개수
        
        Returns:
            학교 개수
        """
        return self.db.query(School).count()
    
    def search(self, keyword: str, state: Optional[str] = None) -> List[School]:
        """
        키워드로 학교 검색
        
        Args:
            keyword: 검색 키워드
            state: 주 이름 (선택)
            
        Returns:
            School 객체 리스트
        """
        query = self.db.query(School).filter(
            or_(
                School.name.ilike(f'%{keyword}%'),
                School.description.ilike(f'%{keyword}%')
            )
        )
        if state:
            query = query.filter(School.state == state)
        return query.all()


class SchoolDocumentRepository:
    """학교 문서 CRUD 작업"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document_data: dict) -> SchoolDocument:
        """학교 문서 생성"""
        try:
            document = SchoolDocument(**document_data)
            self.db.add(document)
            self.db.flush()
            logger.info(f"학교 문서 생성 완료: {document.title} ({document.id})")
            return document
        except Exception as e:
            logger.error(f"학교 문서 생성 실패: {e}")
            raise
    
    def get_by_school(self, school_id: UUID, document_type: Optional[str] = None) -> List[SchoolDocument]:
        """학교 ID로 문서 조회"""
        query = self.db.query(SchoolDocument).filter(SchoolDocument.school_id == school_id)
        if document_type:
            query = query.filter(SchoolDocument.document_type == document_type)
        return query.all()
