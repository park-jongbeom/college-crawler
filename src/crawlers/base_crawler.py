"""
Base Crawler 클래스 - 모든 크롤러의 기본 클래스
"""

import time
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)


class BaseCrawler:
    """웹 크롤러 기본 클래스"""
    
    def __init__(self, base_url: str):
        """
        초기화
        
        Args:
            base_url: 크롤링할 기본 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })
        self.ssl_error_detected: bool = False
        self.ssl_error_message: str = ""
        self.ssl_error_url: str = ""
        self.robots_parser: Optional[RobotFileParser] = None
        self._init_robots_parser()
        
        logger.info(f"크롤러 초기화: {base_url}")
    
    def _init_robots_parser(self) -> None:
        """robots.txt 파서 초기화"""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.debug(f"robots.txt 로드 성공: {robots_url}")
        except Exception as e:
            logger.warning(f"robots.txt 로드 실패 (무시하고 진행): {e}")
            self.robots_parser = None
    
    def can_fetch(self, url: str) -> bool:
        """
        URL 크롤링 가능 여부 확인 (robots.txt 기준)
        
        Args:
            url: 확인할 URL
            
        Returns:
            크롤링 가능 여부
        """
        if not self.robots_parser:
            return True
        
        try:
            return self.robots_parser.can_fetch(config.USER_AGENT, url)
        except Exception as e:
            logger.warning(f"robots.txt 확인 실패 (허용으로 간주): {e}")
            return True
    
    def fetch(self, url: str, retry: int = 0) -> Optional[requests.Response]:
        """
        URL에서 HTML 가져오기
        
        Args:
            url: 요청할 URL
            retry: 현재 재시도 횟수
            
        Returns:
            Response 객체 또는 None
        """
        # Robots.txt 확인
        if not self.can_fetch(url):
            logger.warning(f"robots.txt에 의해 차단됨: {url}")
            return None
        
        try:
            logger.info(f"요청: {url}")
            response = self.session.get(
                url,
                timeout=config.CRAWL_TIMEOUT
            )
            response.raise_for_status()
            
            # 크롤링 간격 대기
            time.sleep(config.CRAWL_DELAY)
            
            logger.info(f"응답 성공: {url} (상태 코드: {response.status_code})")
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"타임아웃: {url}")
            return self._retry_fetch(url, retry)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 오류: {url} - {e}")
            if e.response.status_code in [429, 503]:  # Rate limit or Service unavailable
                return self._retry_fetch(url, retry, delay=10)
            return None

        except requests.exceptions.SSLError as e:
            # SSL 검증 오류는 재시도해도 동일하게 실패하는 경우가 대부분이라 즉시 중단
            self.ssl_error_detected = True
            self.ssl_error_message = str(e)
            self.ssl_error_url = url
            logger.error(f"SSL 검증 실패: {url} - {e}")
            logger.warning(f"SSL 인증서 문제로 요청 중단: {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"요청 실패: {url} - {e}")
            return self._retry_fetch(url, retry)
    
    def _retry_fetch(self, url: str, retry: int, delay: int = 5) -> Optional[requests.Response]:
        """
        재시도 로직
        
        Args:
            url: 요청할 URL
            retry: 현재 재시도 횟수
            delay: 대기 시간 (초)
            
        Returns:
            Response 객체 또는 None
        """
        if retry < config.MAX_RETRY:
            logger.info(f"재시도 {retry + 1}/{config.MAX_RETRY}: {url}")
            time.sleep(delay)
            return self.fetch(url, retry + 1)
        else:
            logger.error(f"최대 재시도 횟수 초과: {url}")
            return None
    
    def get_absolute_url(self, relative_url: str) -> str:
        """
        상대 URL을 절대 URL로 변환
        
        Args:
            relative_url: 상대 URL
            
        Returns:
            절대 URL
        """
        return urljoin(self.base_url, relative_url)
    
    def close(self) -> None:
        """세션 종료"""
        self.session.close()
        logger.info("크롤러 세션 종료")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()
