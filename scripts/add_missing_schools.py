#!/usr/bin/env python3
"""
칼리지 리스트 문서를 기반으로 빠진 학교들을 DB에 추가하는 스크립트
"""

import sys
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.connection import get_db
from database.repository import SchoolRepository
from database.models import School
from utils.logger import setup_logger

logger = setup_logger(__name__)


# 캘리포니아 Community Colleges
CA_SCHOOLS = [
    {"name": "American River College", "city": "Sacramento", "state": "CA", "type": "community_college", "website": "https://arc.losrios.edu"},
    {"name": "Cerritos College", "city": "Norwalk", "state": "CA", "type": "community_college", "website": "https://www.cerritos.edu", "international_email": "international@cerritos.edu", "international_phone": "+1-562-860-2451"},
    {"name": "College of San Mateo", "city": "San Mateo", "state": "CA", "type": "community_college", "website": "https://collegeofsanmateo.edu"},
    {"name": "Saddleback College", "city": "Mission Viejo", "state": "CA", "type": "community_college", "website": "https://www.saddleback.edu"},
    {"name": "Santa Ana College", "city": "Santa Ana", "state": "CA", "type": "community_college", "website": "https://www.sac.edu"},
    {"name": "Chaffey College", "city": "Rancho Cucamonga", "state": "CA", "type": "community_college", "website": "https://www.chaffey.edu", "international_email": "international@chaffey.edu", "international_phone": "+1-909-652-7478"},
    {"name": "Norco College", "city": "Norco", "state": "CA", "type": "community_college", "website": "https://www.norcocollege.edu"},
    {"name": "Evergreen Valley College", "city": "San Jose", "state": "CA", "type": "community_college", "website": "https://www.evc.edu", "international_email": "international@evc.edu", "international_phone": "+1-408-274-7900"},
    {"name": "West Hills College-Lemoore", "city": "Lemoore", "state": "CA", "type": "community_college", "website": "https://www.westhillscollege.com"},
    {"name": "San Jose City College", "city": "San Jose", "state": "CA", "type": "community_college", "website": "https://www.sjcc.edu", "international_email": "international@sjcc.edu", "international_phone": "+1-408-298-2181"},
    {"name": "Mission College", "city": "Santa Clara", "state": "CA", "type": "community_college", "website": "https://www.missioncollege.edu", "international_email": "international@missioncollege.edu", "international_phone": "+1-408-855-5246"},
    {"name": "Contra Costa College", "city": "San Pablo", "state": "CA", "type": "community_college", "website": "https://www.contracosta.edu", "international_email": "international@contracosta.edu", "international_phone": "+1-510-235-7800"},
    {"name": "Fresno City College", "city": "Fresno", "state": "CA", "type": "community_college", "website": "https://www.fresnocitycollege.edu", "international_email": "international@fresnocitycollege.edu", "international_phone": "+1-559-442-4600"},
    {"name": "Allan Hancock College", "city": "Santa Maria", "state": "CA", "type": "community_college", "website": "https://www.hancockcollege.edu"},
    {"name": "Antelope Valley College", "city": "Lancaster", "state": "CA", "type": "community_college", "website": "https://www.avc.edu"},
    {"name": "Cuyamaca College", "city": "El Cajon", "state": "CA", "type": "community_college", "website": "https://www.cuyamaca.edu"},
    {"name": "San Bernardino Valley College", "city": "San Bernardino", "state": "CA", "type": "community_college", "website": "https://www.valleycollege.edu", "international_email": "international@valleycollege.edu", "international_phone": "+1-909-384-4400"},
    {"name": "Cypress College", "city": "Cypress", "state": "CA", "type": "community_college", "website": "https://www.cypresscollege.edu", "international_email": "international@cypresscollege.edu", "international_phone": "+1-714-484-7000"},
    {"name": "Palomar College", "city": "San Marcos", "state": "CA", "type": "community_college", "website": "https://www.palomar.edu", "international_email": "international@palomar.edu", "international_phone": "+1-760-744-1150"},
    {"name": "Ventura College", "city": "Ventura", "state": "CA", "type": "community_college", "website": "https://www.venturacollege.edu", "international_email": "international@venturacollege.edu", "international_phone": "+1-805-289-6000"},
    {"name": "Glendale Community College", "city": "Glendale", "state": "CA", "type": "community_college", "website": "https://www.glendale.edu", "international_email": "iso@glendale.edu", "international_phone": "+1-818-240-1000"},
    {"name": "MiraCosta College", "city": "Oceanside", "state": "CA", "type": "community_college", "website": "https://www.miracosta.edu", "international_email": "international@miracosta.edu", "international_phone": "+1-760-757-2121"},
    {"name": "Long Beach City College", "city": "Long Beach", "state": "CA", "type": "community_college", "website": "https://www.lbcc.edu", "international_email": "iso@lbcc.edu", "international_phone": "+1-562-938-4742"},
    {"name": "Golden West College", "city": "Huntington Beach", "state": "CA", "type": "community_college", "website": "https://www.goldenwestcollege.edu", "international_email": "international@gwc.cccd.edu", "international_phone": "+1-714-895-8156"},
    {"name": "Foothill College", "city": "Los Altos Hills", "state": "CA", "type": "community_college", "website": "https://www.foothill.edu", "international_email": "international@foothill.edu", "international_phone": "+1-650-949-7241"},
    {"name": "Ohlone College", "city": "Fremont", "state": "CA", "type": "community_college", "website": "https://www.ohlone.edu", "international_email": "international@ohlone.edu", "international_phone": "+1-510-659-6000"},
    {"name": "Diablo Valley College", "city": "Pleasant Hill", "state": "CA", "type": "community_college", "website": "https://www.dvc.edu", "international_email": "iso@dvc.edu", "international_phone": "+1-925-685-1230"},
    {"name": "Victor Valley College", "city": "Victorville", "state": "CA", "type": "community_college", "website": "https://www.vvc.edu", "international_email": "international@vvc.edu", "international_phone": "+1-760-245-4271"},
    {"name": "Monterey Peninsula College", "city": "Monterey", "state": "CA", "type": "community_college", "website": "https://www.mpc.edu", "international_email": "international@mpc.edu", "international_phone": "+1-831-646-4000"},
    {"name": "Berkeley City College", "city": "Berkeley", "state": "CA", "type": "community_college", "website": "https://www.berkeleycitycollege.edu"},
    {"name": "Butte College", "city": "Oroville", "state": "CA", "type": "community_college", "website": "https://www.butte.edu"},
    {"name": "Cabrillo College", "city": "Aptos", "state": "CA", "type": "community_college", "website": "https://www.cabrillo.edu"},
    {"name": "Barstow Community College", "city": "Barstow", "state": "CA", "type": "community_college", "website": "https://www.barstow.edu"},
    {"name": "Lake Tahoe Community College", "city": "South Lake Tahoe", "state": "CA", "type": "community_college", "website": "https://www.ltcc.edu"},
    {"name": "Los Angeles City College", "city": "Los Angeles", "state": "CA", "type": "community_college", "website": "https://www.lacitycollege.edu"},
    {"name": "Los Angeles Harbor College", "city": "Wilmington", "state": "CA", "type": "community_college", "website": "https://www.lahc.edu"},
    {"name": "Mt. San Jacinto College", "city": "Menifee", "state": "CA", "type": "community_college", "website": "https://www.msjc.edu"},
    {"name": "City College of San Francisco", "city": "San Francisco", "state": "CA", "type": "community_college", "website": "https://www.ccsf.edu"},
]

# 텍사스 Community Colleges
TX_SCHOOLS = [
    {"name": "Blinn College", "city": "Bryan", "state": "TX", "type": "community_college", "website": "https://www.blinn.edu", "international_email": "international@blinn.edu", "international_phone": "+1-979-830-4150"},
    {"name": "Del Mar College", "city": "Corpus Christi", "state": "TX", "type": "community_college", "website": "https://www.delmar.edu", "international_email": "international@delmar.edu", "international_phone": "+1-361-698-1200"},
    {"name": "South Texas College", "city": "McAllen", "state": "TX", "type": "community_college", "website": "https://www.southtexascollege.edu", "international_email": "international@southtexascollege.edu", "international_phone": "+1-956-872-2110"},
    {"name": "Amarillo College", "city": "Amarillo", "state": "TX", "type": "community_college", "website": "https://www.actx.edu", "international_email": "international@actx.edu", "international_phone": "+1-806-371-5000"},
    {"name": "Lee College", "city": "Baytown", "state": "TX", "type": "community_college", "website": "https://www.lee.edu", "international_email": "international@lee.edu", "international_phone": "+1-281-425-6311"},
    {"name": "Galveston College", "city": "Galveston", "state": "TX", "type": "community_college", "website": "https://www.gc.edu", "international_email": "international@gc.edu", "international_phone": "+1-409-944-1215"},
    {"name": "Weatherford College", "city": "Weatherford", "state": "TX", "type": "community_college", "website": "https://www.wc.edu", "international_email": "international@wc.edu", "international_phone": "+1-817-598-6200"},
    {"name": "Paris Junior College", "city": "Paris", "state": "TX", "type": "community_college", "website": "https://www.parisjc.edu", "international_email": "international@parisjc.edu", "international_phone": "+1-903-785-7661"},
    {"name": "Texarkana College", "city": "Texarkana", "state": "TX", "type": "community_college", "website": "https://www.texarkanacollege.edu"},
    {"name": "Western Texas College", "city": "Snyder", "state": "TX", "type": "community_college", "website": "https://www.wtc.edu"},
    {"name": "North Central Texas College", "city": "Gainesville", "state": "TX", "type": "community_college", "website": "https://www.nctc.edu"},
    {"name": "Trinity Valley Community College", "city": "Athens", "state": "TX", "type": "community_college", "website": "https://www.tvcc.edu"},
    {"name": "Tyler Junior College", "city": "Tyler", "state": "TX", "type": "community_college", "website": "https://www.tjc.edu", "international_email": "international@tjc.edu", "international_phone": "+1-903-510-3301"},
    {"name": "Texas Southmost College", "city": "Brownsville", "state": "TX", "type": "community_college", "website": "https://www.tsc.edu"},
    {"name": "Cedar Valley College", "city": "Lancaster", "state": "TX", "type": "community_college", "website": "https://www.cedarvalleycollege.edu"},
    {"name": "McLennan Community College", "city": "Waco", "state": "TX", "type": "community_college", "website": "https://www.mclennan.edu", "international_email": "international@mclennan.edu", "international_phone": "+1-254-299-8452"},
    {"name": "Lamar State College", "city": "Beaumont", "state": "TX", "type": "community_college", "website": "https://www.lamarpa.edu"},
    {"name": "Howard College", "city": "Big Spring", "state": "TX", "type": "community_college", "website": "https://www.howardcollege.edu"},
    {"name": "Victoria College", "city": "Victoria", "state": "TX", "type": "community_college", "website": "https://www.victoriacollege.edu"},
    {"name": "Kilgore College", "city": "Kilgore", "state": "TX", "type": "community_college", "website": "https://www.kilgore.edu"},
    {"name": "Central Texas College", "city": "Killeen", "state": "TX", "type": "community_college", "website": "https://www.ctcd.edu"},
    {"name": "Alvin Community College", "city": "Alvin", "state": "TX", "type": "community_college", "website": "https://www.alvincollege.edu"},
    {"name": "Hill College", "city": "Hillsboro", "state": "TX", "type": "community_college", "website": "https://www.hillcollege.edu"},
    {"name": "Coastal Bend College", "city": "Beeville", "state": "TX", "type": "community_college", "website": "https://www.coastalbend.edu"},
]


def add_schools(db_session, schools_data, state_name):
    """학교 데이터를 DB에 추가"""
    repo = SchoolRepository(db_session)
    added_count = 0
    skipped_count = 0
    
    for school_data in schools_data:
        # 이미 존재하는지 확인
        existing = repo.get_by_name(school_data["name"], school_data["state"])
        
        if existing:
            logger.info(f"이미 존재함: {school_data['name']}")
            skipped_count += 1
            continue
        
        try:
            # 학교 추가
            school = repo.create(school_data)
            db_session.commit()
            logger.info(f"추가 완료: {school.name} ({school.city}, {school.state})")
            added_count += 1
        except Exception as e:
            logger.error(f"추가 실패: {school_data['name']} - {e}")
            db_session.rollback()
    
    logger.info(f"\n{state_name} 처리 완료: {added_count}개 추가, {skipped_count}개 스킵")
    return added_count, skipped_count


def main():
    """메인 실행 함수"""
    logger.info("=" * 80)
    logger.info("빠진 학교 추가 스크립트 시작")
    logger.info("=" * 80)
    
    db = next(get_db())
    
    try:
        # 캘리포니아 학교 추가
        logger.info("\n[1] 캘리포니아 학교 추가 중...")
        ca_added, ca_skipped = add_schools(db, CA_SCHOOLS, "캘리포니아")
        
        # 텍사스 학교 추가
        logger.info("\n[2] 텍사스 학교 추가 중...")
        tx_added, tx_skipped = add_schools(db, TX_SCHOOLS, "텍사스")
        
        # 최종 통계
        logger.info("\n" + "=" * 80)
        logger.info("최종 통계:")
        logger.info(f"  캘리포니아: {ca_added}개 추가, {ca_skipped}개 스킵")
        logger.info(f"  텍사스: {tx_added}개 추가, {tx_skipped}개 스킵")
        logger.info(f"  총 {ca_added + tx_added}개 학교 추가됨")
        logger.info("=" * 80)
        
        # 최종 학교 수 확인
        repo = SchoolRepository(db)
        total_count = repo.count()
        logger.info(f"\n현재 DB 총 학교 수: {total_count}개")
        
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류 발생: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
