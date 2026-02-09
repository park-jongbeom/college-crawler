"""
시설 정보 파서
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class FacilityParser:
    """시설 정보 파싱 클래스"""
    
    # 시설 키워드
    FACILITY_KEYWORDS = {
        'dormitory': ['dormitory', 'dorm', 'housing', 'residence hall'],
        'dining': ['dining', 'cafeteria', 'food service', 'restaurant'],
        'gym': ['gym', 'fitness', 'recreation', 'athletic', 'sports center'],
        'library': ['library', 'learning resource'],
        'lab': ['laboratory', 'lab', 'computer lab'],
        'entertainment': ['theater', 'cinema', 'entertainment', 'student center']
    }
    
    @staticmethod
    def parse_facilities(html: str) -> Dict[str, bool]:
        """
        시설 정보 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            시설 정보 딕셔너리 (있으면 True, 없으면 False)
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        facilities = {}
        for facility_type, keywords in FacilityParser.FACILITY_KEYWORDS.items():
            found = any(keyword in text for keyword in keywords)
            facilities[facility_type] = found
        
        return facilities
    
    @staticmethod
    def parse_facility_details(html: str) -> Dict[str, Optional[str]]:
        """
        시설 상세 정보 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            시설 상세 정보 딕셔너리
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        details = {}
        
        # facilities, campus life 섹션 찾기
        facility_sections = soup.find_all(['div', 'section'], 
                                         text=re.compile(r'facilities|campus life|student life', re.I))
        
        for section in facility_sections:
            # 섹션 내용 추출
            content = section.get_text(strip=True)
            
            for facility_type, keywords in FacilityParser.FACILITY_KEYWORDS.items():
                if any(keyword in content.lower() for keyword in keywords):
                    # 해당 시설에 대한 설명 추출 (간단히)
                    details[facility_type] = content[:200] + '...' if len(content) > 200 else content
        
        return details
