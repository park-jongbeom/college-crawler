#!/usr/bin/env python3
"""
psycopg2를 직접 사용하여 학교 데이터를 추가하는 스크립트
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# DB 연결 정보
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'ls-584229d62cccd625a5fa723267dbdbc614b3b0e5.c9wi0gwweu9n.ap-northeast-2.rds.amazonaws.com'),
    'port': int(os.getenv('DATABASE_PORT', 5432)),
    'database': os.getenv('DATABASE_NAME', 'ga_db'),
    'user': os.getenv('DATABASE_USER', 'dbmasteruser'),
    'password': os.getenv('DATABASE_PASSWORD', 'w,*i.uAk7f^Gj;Gk`3O`oqZx3`0fj9Vm')
}

# 캘리포니아 학교 데이터
CA_SCHOOLS = [
    ("American River College", "Sacramento", "CA", "community_college", "https://arc.losrios.edu", None, None),
    ("Cerritos College", "Norwalk", "CA", "community_college", "https://www.cerritos.edu", "international@cerritos.edu", "+1-562-860-2451"),
    ("College of San Mateo", "San Mateo", "CA", "community_college", "https://collegeofsanmateo.edu", None, None),
    ("Saddleback College", "Mission Viejo", "CA", "community_college", "https://www.saddleback.edu", None, None),
    ("Santa Ana College", "Santa Ana", "CA", "community_college", "https://www.sac.edu", None, None),
    ("Chaffey College", "Rancho Cucamonga", "CA", "community_college", "https://www.chaffey.edu", "international@chaffey.edu", "+1-909-652-7478"),
    ("Norco College", "Norco", "CA", "community_college", "https://www.norcocollege.edu", None, None),
    ("Evergreen Valley College", "San Jose", "CA", "community_college", "https://www.evc.edu", "international@evc.edu", "+1-408-274-7900"),
    ("West Hills College-Lemoore", "Lemoore", "CA", "community_college", "https://www.westhillscollege.com", None, None),
    ("San Jose City College", "San Jose", "CA", "community_college", "https://www.sjcc.edu", "international@sjcc.edu", "+1-408-298-2181"),
    ("Mission College", "Santa Clara", "CA", "community_college", "https://www.missioncollege.edu", "international@missioncollege.edu", "+1-408-855-5246"),
    ("Contra Costa College", "San Pablo", "CA", "community_college", "https://www.contracosta.edu", "international@contracosta.edu", "+1-510-235-7800"),
    ("Fresno City College", "Fresno", "CA", "community_college", "https://www.fresnocitycollege.edu", "international@fresnocitycollege.edu", "+1-559-442-4600"),
    ("Allan Hancock College", "Santa Maria", "CA", "community_college", "https://www.hancockcollege.edu", None, None),
    ("Antelope Valley College", "Lancaster", "CA", "community_college", "https://www.avc.edu", None, None),
    ("Cuyamaca College", "El Cajon", "CA", "community_college", "https://www.cuyamaca.edu", None, None),
    ("San Bernardino Valley College", "San Bernardino", "CA", "community_college", "https://www.valleycollege.edu", "international@valleycollege.edu", "+1-909-384-4400"),
    ("Cypress College", "Cypress", "CA", "community_college", "https://www.cypresscollege.edu", "international@cypresscollege.edu", "+1-714-484-7000"),
    ("Palomar College", "San Marcos", "CA", "community_college", "https://www.palomar.edu", "international@palomar.edu", "+1-760-744-1150"),
    ("Ventura College", "Ventura", "CA", "community_college", "https://www.venturacollege.edu", "international@venturacollege.edu", "+1-805-289-6000"),
    ("Glendale Community College", "Glendale", "CA", "community_college", "https://www.glendale.edu", "iso@glendale.edu", "+1-818-240-1000"),
    ("MiraCosta College", "Oceanside", "CA", "community_college", "https://www.miracosta.edu", "international@miracosta.edu", "+1-760-757-2121"),
    ("Long Beach City College", "Long Beach", "CA", "community_college", "https://www.lbcc.edu", "iso@lbcc.edu", "+1-562-938-4742"),
    ("Golden West College", "Huntington Beach", "CA", "community_college", "https://www.goldenwestcollege.edu", "international@gwc.cccd.edu", "+1-714-895-8156"),
    ("Foothill College", "Los Altos Hills", "CA", "community_college", "https://www.foothill.edu", "international@foothill.edu", "+1-650-949-7241"),
    ("Ohlone College", "Fremont", "CA", "community_college", "https://www.ohlone.edu", "international@ohlone.edu", "+1-510-659-6000"),
    ("Diablo Valley College", "Pleasant Hill", "CA", "community_college", "https://www.dvc.edu", "iso@dvc.edu", "+1-925-685-1230"),
    ("Victor Valley College", "Victorville", "CA", "community_college", "https://www.vvc.edu", "international@vvc.edu", "+1-760-245-4271"),
    ("Monterey Peninsula College", "Monterey", "CA", "community_college", "https://www.mpc.edu", "international@mpc.edu", "+1-831-646-4000"),
    ("Berkeley City College", "Berkeley", "CA", "community_college", "https://www.berkeleycitycollege.edu", None, None),
    ("Butte College", "Oroville", "CA", "community_college", "https://www.butte.edu", None, None),
    ("Cabrillo College", "Aptos", "CA", "community_college", "https://www.cabrillo.edu", None, None),
    ("Barstow Community College", "Barstow", "CA", "community_college", "https://www.barstow.edu", None, None),
    ("Lake Tahoe Community College", "South Lake Tahoe", "CA", "community_college", "https://www.ltcc.edu", None, None),
    ("Los Angeles City College", "Los Angeles", "CA", "community_college", "https://www.lacitycollege.edu", None, None),
    ("Los Angeles Harbor College", "Wilmington", "CA", "community_college", "https://www.lahc.edu", None, None),
    ("Mt. San Jacinto College", "Menifee", "CA", "community_college", "https://www.msjc.edu", None, None),
    ("City College of San Francisco", "San Francisco", "CA", "community_college", "https://www.ccsf.edu", None, None),
]

# 텍사스 학교 데이터
TX_SCHOOLS = [
    ("Blinn College", "Bryan", "TX", "community_college", "https://www.blinn.edu", "international@blinn.edu", "+1-979-830-4150"),
    ("Del Mar College", "Corpus Christi", "TX", "community_college", "https://www.delmar.edu", "international@delmar.edu", "+1-361-698-1200"),
    ("South Texas College", "McAllen", "TX", "community_college", "https://www.southtexascollege.edu", "international@southtexascollege.edu", "+1-956-872-2110"),
    ("Amarillo College", "Amarillo", "TX", "community_college", "https://www.actx.edu", "international@actx.edu", "+1-806-371-5000"),
    ("Lee College", "Baytown", "TX", "community_college", "https://www.lee.edu", "international@lee.edu", "+1-281-425-6311"),
    ("Galveston College", "Galveston", "TX", "community_college", "https://www.gc.edu", "international@gc.edu", "+1-409-944-1215"),
    ("Weatherford College", "Weatherford", "TX", "community_college", "https://www.wc.edu", "international@wc.edu", "+1-817-598-6200"),
    ("Paris Junior College", "Paris", "TX", "community_college", "https://www.parisjc.edu", "international@parisjc.edu", "+1-903-785-7661"),
    ("Texarkana College", "Texarkana", "TX", "community_college", "https://www.texarkanacollege.edu", None, None),
    ("Western Texas College", "Snyder", "TX", "community_college", "https://www.wtc.edu", None, None),
    ("North Central Texas College", "Gainesville", "TX", "community_college", "https://www.nctc.edu", None, None),
    ("Trinity Valley Community College", "Athens", "TX", "community_college", "https://www.tvcc.edu", None, None),
    ("Tyler Junior College", "Tyler", "TX", "community_college", "https://www.tjc.edu", "international@tjc.edu", "+1-903-510-3301"),
    ("Texas Southmost College", "Brownsville", "TX", "community_college", "https://www.tsc.edu", None, None),
    ("Cedar Valley College", "Lancaster", "TX", "community_college", "https://www.cedarvalleycollege.edu", None, None),
    ("McLennan Community College", "Waco", "TX", "community_college", "https://www.mclennan.edu", "international@mclennan.edu", "+1-254-299-8452"),
    ("Lamar State College", "Beaumont", "TX", "community_college", "https://www.lamarpa.edu", None, None),
    ("Howard College", "Big Spring", "TX", "community_college", "https://www.howardcollege.edu", None, None),
    ("Victoria College", "Victoria", "TX", "community_college", "https://www.victoriacollege.edu", None, None),
    ("Kilgore College", "Kilgore", "TX", "community_college", "https://www.kilgore.edu", None, None),
    ("Central Texas College", "Killeen", "TX", "community_college", "https://www.ctcd.edu", None, None),
    ("Alvin Community College", "Alvin", "TX", "community_college", "https://www.alvincollege.edu", None, None),
    ("Hill College", "Hillsboro", "TX", "community_college", "https://www.hillcollege.edu", None, None),
    ("Coastal Bend College", "Beeville", "TX", "community_college", "https://www.coastalbend.edu", None, None),
]


def main():
    print("=" * 80)
    print("학교 데이터 추가 스크립트 시작")
    print("=" * 80)
    
    try:
        # DB 연결
        print("\n데이터베이스 연결 중...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()
        print("✓ 연결 성공")
        
        # 현재 학교 수 확인
        cur.execute("SELECT COUNT(*) FROM schools")
        before_count = cur.fetchone()[0]
        print(f"\n현재 학교 수: {before_count}개")
        
        ca_added = 0
        ca_skipped = 0
        
        # 캘리포니아 학교 추가
        print("\n[1] 캘리포니아 학교 추가 중...")
        for school in CA_SCHOOLS:
            name, city, state, type_, website, email, phone = school
            
            # 이미 존재하는지 확인
            cur.execute("SELECT id FROM schools WHERE name = %s AND state = %s", (name, state))
            if cur.fetchone():
                print(f"  ⊘ 이미 존재: {name}")
                ca_skipped += 1
                continue
            
            # 학교 추가
            cur.execute("""
                INSERT INTO schools (id, name, city, state, type, website, international_email, international_phone, created_at, updated_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (name, city, state, type_, website, email, phone))
            print(f"  ✓ 추가: {name} ({city})")
            ca_added += 1
        
        conn.commit()
        print(f"\n캘리포니아 완료: {ca_added}개 추가, {ca_skipped}개 스킵")
        
        tx_added = 0
        tx_skipped = 0
        
        # 텍사스 학교 추가
        print("\n[2] 텍사스 학교 추가 중...")
        for school in TX_SCHOOLS:
            name, city, state, type_, website, email, phone = school
            
            # 이미 존재하는지 확인
            cur.execute("SELECT id FROM schools WHERE name = %s AND state = %s", (name, state))
            if cur.fetchone():
                print(f"  ⊘ 이미 존재: {name}")
                tx_skipped += 1
                continue
            
            # 학교 추가
            cur.execute("""
                INSERT INTO schools (id, name, city, state, type, website, international_email, international_phone, created_at, updated_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (name, city, state, type_, website, email, phone))
            print(f"  ✓ 추가: {name} ({city})")
            tx_added += 1
        
        conn.commit()
        print(f"\n텍사스 완료: {tx_added}개 추가, {tx_skipped}개 스킵")
        
        # 최종 학교 수 확인
        cur.execute("SELECT COUNT(*) FROM schools")
        after_count = cur.fetchone()[0]
        
        # 통계 출력
        print("\n" + "=" * 80)
        print("최종 통계:")
        print(f"  이전 학교 수: {before_count}개")
        print(f"  추가된 학교 수: {ca_added + tx_added}개")
        print(f"    - 캘리포니아: {ca_added}개")
        print(f"    - 텍사스: {tx_added}개")
        print(f"  현재 학교 수: {after_count}개")
        print("=" * 80)
        
        cur.close()
        conn.close()
        print("\n✓ 완료!")
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
