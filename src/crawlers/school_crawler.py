"""
학교 정보 크롤러
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.crawlers.base_crawler import BaseCrawler
from src.crawlers.parsers.contact_parser import ContactParser
from src.crawlers.parsers.facility_parser import FacilityParser
from src.crawlers.parsers.program_parser import ProgramParser
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchoolCrawler(BaseCrawler):
    """학교 정보 크롤러"""
    
    def __init__(self, school_name: str, website: str):
        """
        초기화
        
        Args:
            school_name: 학교 이름
            website: 학교 웹사이트 URL
        """
        super().__init__(website)
        self.school_name = school_name
        self.data: Dict[str, Any] = {
            'name': school_name,
            'website': website,
            'crawled_data': {}
        }
    
    def crawl_all(self) -> Dict[str, Any]:
        """
        모든 정보 크롤링
        
        Returns:
            크롤링된 데이터 딕셔너리
        """
        logger.info(f"=== {self.school_name} 크롤링 시작 ===")
        
        try:
            # 1. 메인 페이지 크롤링
            self._crawl_homepage()
            
            # 2. International Students 페이지 크롤링
            self._crawl_international_page()
            
            # 3. Programs 페이지 크롤링
            self._crawl_programs_page()
            
            # 4. Campus Life 페이지 크롤링
            self._crawl_campus_life_page()
            
            logger.info(f"✅ {self.school_name} 크롤링 완료")
            
        except Exception as e:
            logger.error(f"❌ {self.school_name} 크롤링 실패: {e}")
        
        return self.data
    
    def _crawl_homepage(self) -> None:
        """메인 페이지 크롤링"""
        logger.info(f"메인 페이지 크롤링: {self.base_url}")
        
        response = self.fetch(self.base_url)
        if not response:
            logger.warning("메인 페이지 응답 없음")
            return
        
        html = response.text
        
        # 기본 연락처 정보 파싱
        contact_info = ContactParser.parse_contact_info(html)
        self.data['crawled_data'].update(contact_info)
        
        logger.info(f"메인 페이지 파싱 완료: {contact_info}")
    
    def _crawl_international_page(self) -> None:
        """International Students 페이지 크롤링"""
        # International 관련 가능한 URL 패턴
        patterns = [
            '/international',
            '/international-students',
            '/admissions/international',
            '/students/international',
            '/global',
            '/international-programs'
        ]
        
        for pattern in patterns:
            url = self.get_absolute_url(pattern)
            logger.info(f"International 페이지 시도: {url}")
            
            response = self.fetch(url)
            if response and response.status_code == 200:
                html = response.text
                
                # 연락처 재파싱 (더 정확한 정보 가능)
                contact_info = ContactParser.parse_contact_info(html)
                if contact_info.get('international_email'):
                    self.data['crawled_data'].update(contact_info)
                
                # 유학생 지원 정보
                support_info = ProgramParser.parse_international_support(html)
                self.data['crawled_data']['international_support'] = support_info
                
                # ESL 프로그램
                esl_info = ProgramParser.parse_esl_program(html)
                self.data['crawled_data']['esl_program'] = esl_info
                
                logger.info(f"✅ International 페이지 파싱 완료")
                break
        else:
            logger.warning("International 페이지를 찾을 수 없음")
    
    def _crawl_programs_page(self) -> None:
        """Programs/Academics 페이지 크롤링"""
        patterns = [
            '/programs',
            '/academics',
            '/academics/programs',
            '/degrees',
            '/programs-of-study'
        ]
        
        for pattern in patterns:
            url = self.get_absolute_url(pattern)
            logger.info(f"Programs 페이지 시도: {url}")
            
            response = self.fetch(url)
            if response and response.status_code == 200:
                html = response.text
                
                # 전공 목록
                majors = ProgramParser.parse_majors(html)
                if majors:
                    self.data['crawled_data']['majors'] = majors
                
                # ESL 프로그램 (아직 없으면)
                if 'esl_program' not in self.data['crawled_data']:
                    esl_info = ProgramParser.parse_esl_program(html)
                    self.data['crawled_data']['esl_program'] = esl_info
                
                logger.info(f"✅ Programs 페이지 파싱 완료: {len(majors)}개 전공")
                break
        else:
            logger.warning("Programs 페이지를 찾을 수 없음")
    
    def _crawl_campus_life_page(self) -> None:
        """Campus Life/Facilities 페이지 크롤링"""
        patterns = [
            '/campus-life',
            '/student-life',
            '/campus',
            '/facilities',
            '/about/campus'
        ]
        
        for pattern in patterns:
            url = self.get_absolute_url(pattern)
            logger.info(f"Campus Life 페이지 시도: {url}")
            
            response = self.fetch(url)
            if response and response.status_code == 200:
                html = response.text
                
                # 시설 정보
                facilities = FacilityParser.parse_facilities(html)
                self.data['crawled_data']['facilities'] = facilities
                
                # 시설 상세
                facility_details = FacilityParser.parse_facility_details(html)
                if facility_details:
                    self.data['crawled_data']['facility_details'] = facility_details
                
                logger.info(f"✅ Campus Life 페이지 파싱 완료")
                break
        else:
            logger.warning("Campus Life 페이지를 찾을 수 없음")
    
    def save_to_json(self, output_dir: Path) -> None:
        """
        크롤링 결과를 JSON 파일로 저장
        
        Args:
            output_dir: 출력 디렉토리
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명: 학교 이름 (공백을 언더스코어로)
        filename = self.school_name.replace(' ', '_').replace('–', '-') + '.json'
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 결과 저장: {filepath}")
