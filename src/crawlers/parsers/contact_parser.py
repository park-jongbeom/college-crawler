"""
연락처 정보 파서
"""

import re
from typing import Optional, Dict
from bs4 import BeautifulSoup


class ContactParser:
    """연락처 정보 파싱 클래스"""
    
    # 이메일 패턴
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    # 전화번호 패턴 (미국)
    PHONE_PATTERN = re.compile(r'[\+]?[1]?[-.\s]?(\()?[0-9]{3}(\))?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}')
    
    @staticmethod
    def parse_email(html: str) -> Optional[str]:
        """
        HTML에서 이메일 주소 추출
        
        Args:
            html: HTML 문자열
            
        Returns:
            이메일 주소 또는 None
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. mailto: 링크에서 찾기
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').split('?')[0]
            return email.strip()
        
        # 2. international, admissions 키워드가 있는 섹션에서 찾기
        sections = soup.find_all(['div', 'section', 'article'], 
                                 text=re.compile(r'international|admissions|contact', re.I))
        
        for section in sections:
            text = section.get_text()
            emails = ContactParser.EMAIL_PATTERN.findall(text)
            if emails:
                # international이 포함된 이메일 우선
                intl_emails = [e for e in emails if 'international' in e.lower()]
                if intl_emails:
                    return intl_emails[0]
                return emails[0]
        
        # 3. 전체 텍스트에서 찾기
        text = soup.get_text()
        emails = ContactParser.EMAIL_PATTERN.findall(text)
        if emails:
            # international이 포함된 이메일 우선
            intl_emails = [e for e in emails if 'international' in e.lower()]
            if intl_emails:
                return intl_emails[0]
            return emails[0]
        
        return None
    
    @staticmethod
    def parse_phone(html: str) -> Optional[str]:
        """
        HTML에서 전화번호 추출
        
        Args:
            html: HTML 문자열
            
        Returns:
            전화번호 또는 None
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # international, admissions 키워드가 있는 섹션에서 찾기
        sections = soup.find_all(['div', 'section', 'article'], 
                                 text=re.compile(r'international|admissions|contact', re.I))
        
        for section in sections:
            text = section.get_text()
            phones = ContactParser.PHONE_PATTERN.findall(text)
            if phones:
                # 전화번호 정규화
                phone = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
                return ContactParser._normalize_phone(phone)
        
        # 전체 텍스트에서 찾기
        text = soup.get_text()
        phones = ContactParser.PHONE_PATTERN.findall(text)
        if phones:
            phone = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
            return ContactParser._normalize_phone(phone)
        
        return None
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        전화번호 정규화
        
        Args:
            phone: 원본 전화번호
            
        Returns:
            정규화된 전화번호 (+1-XXX-XXX-XXXX 형식)
        """
        # 숫자만 추출
        digits = re.sub(r'\D', '', phone)
        
        # 국가 코드 추가
        if len(digits) == 10:
            digits = '1' + digits
        
        # 포맷팅
        if len(digits) == 11 and digits[0] == '1':
            return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        
        return phone
    
    @staticmethod
    def parse_contact_info(html: str) -> Dict[str, Optional[str]]:
        """
        연락처 정보 전체 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            연락처 정보 딕셔너리
        """
        return {
            'international_email': ContactParser.parse_email(html),
            'international_phone': ContactParser.parse_phone(html)
        }
