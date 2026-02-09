"""
프로그램 정보 파서 (ESL, 전공 등)
"""

import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup


class ProgramParser:
    """프로그램 정보 파싱 클래스"""
    
    @staticmethod
    def parse_esl_program(html: str) -> Dict[str, Any]:
        """
        ESL 프로그램 정보 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            ESL 프로그램 정보 딕셔너리
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        # ESL 관련 키워드
        esl_keywords = ['esl', 'english as a second language', 'english language', 
                       'ell', 'english learner', 'intensive english']
        
        has_esl = any(keyword in text for keyword in esl_keywords)
        
        if not has_esl:
            return {
                'available': False,
                'description': None
            }
        
        # ESL 섹션 찾기
        esl_sections = soup.find_all(['div', 'section', 'article'], 
                                     text=re.compile(r'esl|english.+second.+language', re.I))
        
        description = None
        if esl_sections:
            description = esl_sections[0].get_text(strip=True)[:300]
        
        return {
            'available': True,
            'description': description
        }
    
    @staticmethod
    def parse_majors(html: str) -> List[str]:
        """
        전공 목록 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            전공 목록
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        majors = []
        
        # programs, majors, degrees 섹션 찾기
        program_sections = soup.find_all(['div', 'section', 'ul'], 
                                        text=re.compile(r'programs|majors|degrees', re.I))
        
        for section in program_sections:
            # 리스트 아이템 찾기
            items = section.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) < 100:  # 너무 긴 텍스트는 제외
                    majors.append(text)
        
        # 중복 제거
        majors = list(set(majors))
        
        return majors[:20]  # 최대 20개
    
    @staticmethod
    def parse_international_support(html: str) -> Dict[str, Any]:
        """
        유학생 지원 정보 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            유학생 지원 정보 딕셔너리
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # international students 섹션 찾기
        intl_sections = soup.find_all(['div', 'section', 'article'], 
                                     text=re.compile(r'international.+student', re.I))
        
        support_info = {
            'available': False,
            'services': [],
            'description': None
        }
        
        if not intl_sections:
            return support_info
        
        support_info['available'] = True
        
        # 지원 서비스 키워드
        service_keywords = [
            'visa support', 'housing assistance', 'orientation',
            'tutoring', 'counseling', 'cultural activities',
            'career services', 'academic advising'
        ]
        
        text = intl_sections[0].get_text().lower()
        
        # 제공하는 서비스 찾기
        found_services = [keyword for keyword in service_keywords if keyword in text]
        support_info['services'] = found_services
        
        # 설명 추출
        support_info['description'] = intl_sections[0].get_text(strip=True)[:300]
        
        return support_info
