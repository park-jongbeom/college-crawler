"""베이스 크롤러 클래스"""
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests
from bs4 import BeautifulSoup


class BaseCrawler(ABC):
    """모든 크롤러의 베이스 클래스"""
    
    def __init__(
        self,
        base_url: str,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        request_delay: float = 2.0
    ):
        """
        Args:
            base_url: 크롤링 대상 기본 URL
            user_agent: User-Agent 헤더
            request_delay: 요청 간 대기 시간 (초)
        """
        self.base_url = base_url
        self.user_agent = user_agent
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
    
    def fetch(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        URL에서 HTML 가져오기
        
        Args:
            url: 요청할 URL
            timeout: 타임아웃 (초)
            
        Returns:
            HTML 문자열 또는 None
        """
        try:
            time.sleep(self.request_delay)  # Rate limiting
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"요청 실패: {url} - {e}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        HTML 파싱
        
        Args:
            html: HTML 문자열
            
        Returns:
            BeautifulSoup 객체
        """
        return BeautifulSoup(html, "lxml")
    
    @abstractmethod
    def parse(self, html: str) -> dict:
        """
        HTML을 파싱하여 데이터 추출 (하위 클래스에서 구현)
        
        Args:
            html: HTML 문자열
            
        Returns:
            추출된 데이터 딕셔너리
        """
        pass
    
    def crawl(self, url: str) -> Optional[dict]:
        """
        크롤링 실행 (fetch + parse)
        
        Args:
            url: 크롤링할 URL
            
        Returns:
            추출된 데이터 또는 None
        """
        html = self.fetch(url)
        if html:
            return self.parse(html)
        return None
