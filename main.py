#!/usr/bin/env python3
"""
College Crawler - Main Entry Point

미국 대학 정보 수집 크롤러의 메인 진입점
"""
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """메인 실행 함수"""
    logger.info("🕷️ College Crawler 시작")
    
    # TODO: 크롤러 실행 로직 구현
    logger.info("크롤러 준비 완료. 구현 대기 중...")
    
    logger.info("✅ College Crawler 종료")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"에러 발생: {e}", exc_info=True)
