#!/usr/bin/env python3
"""
현재 DB에 저장된 학교 목록 확인 스크립트
"""

import sys
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.connection import get_db
from database.repository import SchoolRepository


def main():
    """현재 저장된 학교 목록 조회"""
    db = next(get_db())
    repo = SchoolRepository(db)
    
    schools = repo.get_all(limit=1000)
    
    print(f"현재 DB에 저장된 학교: {len(schools)}개\n")
    print("=" * 80)
    
    # 주별로 그룹화
    ca_schools = [s for s in schools if s.state == 'CA']
    tx_schools = [s for s in schools if s.state == 'TX']
    other_schools = [s for s in schools if s.state not in ['CA', 'TX']]
    
    print(f"\n캘리포니아 (CA): {len(ca_schools)}개")
    for school in sorted(ca_schools, key=lambda x: x.name):
        print(f"  - {school.name} ({school.city})")
    
    print(f"\n텍사스 (TX): {len(tx_schools)}개")
    for school in sorted(tx_schools, key=lambda x: x.name):
        print(f"  - {school.name} ({school.city})")
    
    if other_schools:
        print(f"\n기타: {len(other_schools)}개")
        for school in sorted(other_schools, key=lambda x: x.name):
            print(f"  - {school.name} ({school.state}, {school.city})")
    
    print("\n" + "=" * 80)
    print(f"총 {len(schools)}개 학교")


if __name__ == "__main__":
    main()
