#!/usr/bin/env python
"""
크롤러 테스트 스크립트 - 단일 학교 테스트
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawlers.school_crawler import SchoolCrawler
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_crawler():
    """크롤러 테스트"""
    
    # 테스트할 학교 정보
    test_schools = [
        {
            'name': 'Los Angeles Trade-Technical College',
            'website': 'https://lattc.edu'
        },
        {
            'name': 'Santa Monica College',
            'website': 'https://smc.edu'
        }
    ]
    
    logger.info("🧪 크롤러 테스트 시작\n")
    
    for school in test_schools:
        logger.info(f"\n{'='*60}")
        logger.info(f"테스트: {school['name']}")
        logger.info(f"{'='*60}\n")
        
        try:
            with SchoolCrawler(school['name'], school['website']) as crawler:
                # 크롤링 실행
                data = crawler.crawl_all()

                # 결과 출력
                crawled = data.get('crawled_data', {})
                logger.info(f"\n✅ 크롤링 완료:")
                logger.info(f"  📧 이메일: {crawled.get('international_email', 'N/A')}")
                logger.info(f"  📞 전화: {crawled.get('international_phone', 'N/A')}")
                logger.info(f"  🌍 유학생 지원: {crawled.get('international_support', {}).get('available', False)}")
                logger.info(f"  📚 ESL 프로그램: {crawled.get('esl_program', {}).get('available', False)}")
                logger.info(f"  🎓 전공 수: {len(crawled.get('majors', []))}")
                
                if crawled.get('facilities'):
                    facilities = crawled['facilities']
                    logger.info(f"  🏢 시설:")
                    for facility, available in facilities.items():
                        status = "✓" if available else "✗"
                        logger.info(f"     [{status}] {facility}")
                
        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"\n{'='*60}")
    logger.info("🎉 테스트 완료")
    logger.info(f"{'='*60}\n")


if __name__ == '__main__':
    test_crawler()
