"""
College Crawler 메인 실행 파일
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawlers.school_crawler import SchoolCrawler
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_schools_list(json_file: Path) -> list:
    """
    학교 목록 JSON 파일 로드
    
    Args:
        json_file: JSON 파일 경로
        
    Returns:
        학교 목록
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('schools', [])


def crawl_single_school(name: str, website: str, output_dir: Path) -> None:
    """
    단일 학교 크롤링
    
    Args:
        name: 학교 이름
        website: 웹사이트 URL
        output_dir: 출력 디렉토리
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"크롤링 시작: {name}")
    logger.info(f"{'='*60}\n")
    
    try:
        with SchoolCrawler(name, website) as crawler:
            data = crawler.crawl_all()
            crawler.save_to_json(output_dir)
            
            # 요약 출력
            crawled = data.get('crawled_data', {})
            logger.info(f"\n📊 크롤링 결과 요약:")
            logger.info(f"  - 이메일: {crawled.get('international_email', 'N/A')}")
            logger.info(f"  - 전화: {crawled.get('international_phone', 'N/A')}")
            logger.info(f"  - ESL: {crawled.get('esl_program', {}).get('available', False)}")
            logger.info(f"  - 전공 수: {len(crawled.get('majors', []))}")
            
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")


def crawl_all_schools(json_file: Path, output_dir: Path, limit: int = None) -> None:
    """
    모든 학교 크롤링
    
    Args:
        json_file: 학교 목록 JSON 파일
        output_dir: 출력 디렉토리
        limit: 크롤링할 최대 학교 수 (None이면 전체)
    """
    schools = load_schools_list(json_file)
    
    if limit:
        schools = schools[:limit]
    
    logger.info(f"📚 총 {len(schools)}개 학교 크롤링 시작\n")
    
    success_count = 0
    fail_count = 0
    
    for i, school in enumerate(schools, 1):
        name = school.get('name')
        website = school.get('website')
        
        if not name or not website:
            logger.warning(f"⏭️  건너뜀: 정보 부족 - {school}")
            fail_count += 1
            continue
        
        logger.info(f"\n[{i}/{len(schools)}] {name}")
        
        try:
            crawl_single_school(name, website, output_dir)
            success_count += 1
        except Exception as e:
            logger.error(f"❌ 실패: {e}")
            fail_count += 1
    
    # 최종 결과
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 최종 결과")
    logger.info(f"{'='*60}")
    logger.info(f"✅ 성공: {success_count}개")
    logger.info(f"❌ 실패: {fail_count}개")
    logger.info(f"📁 출력 디렉토리: {output_dir.absolute()}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='College Crawler - 미국 대학 정보 수집')
    
    parser.add_argument('command', choices=['crawl', 'test'], 
                       help='실행할 명령 (crawl: 크롤링 실행, test: 테스트 크롤링)')
    parser.add_argument('--school', type=str, 
                       help='크롤링할 특정 학교 이름')
    parser.add_argument('--website', type=str, 
                       help='학교 웹사이트 URL (--school과 함께 사용)')
    parser.add_argument('--limit', type=int, 
                       help='크롤링할 최대 학교 수')
    parser.add_argument('--output', type=str, default='data/crawled',
                       help='출력 디렉토리 (기본: data/crawled)')
    
    args = parser.parse_args()
    
    # 출력 디렉토리 설정
    project_root = Path(__file__).parent.parent
    output_dir = project_root / args.output
    
    if args.command == 'test':
        # 테스트: 첫 번째 학교만 크롤링
        logger.info("🧪 테스트 모드: 첫 번째 학교만 크롤링")
        json_file = project_root / 'data' / 'schools_initial.json'
        crawl_all_schools(json_file, output_dir, limit=1)
        
    elif args.command == 'crawl':
        if args.school and args.website:
            # 특정 학교 크롤링
            crawl_single_school(args.school, args.website, output_dir)
        else:
            # 전체 학교 크롤링
            json_file = project_root / 'data' / 'schools_initial.json'
            crawl_all_schools(json_file, output_dir, limit=args.limit)


if __name__ == '__main__':
    main()
