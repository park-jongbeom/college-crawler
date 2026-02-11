"""
운영 DB에서 전체 학교 목록을 추출하여 schools_initial.json 생성
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.database.models import School

def export_schools_to_json():
    """DB에서 전체 학교 목록을 추출하여 JSON으로 저장"""
    try:
        with get_db() as db:
            schools = db.query(School).all()
            
            schools_data = {
                "schools": [
                    {
                        "name": school.name,
                        "type": school.type,
                        "state": school.state or "",
                        "city": school.city or "",
                        "website": school.website or "",
                        "international_email": school.international_email or None,
                        "international_phone": school.international_phone or None,
                        "tuition": school.tuition or None,
                        "description": school.description or ""
                    }
                    for school in schools
                    if school.website  # 웹사이트가 있는 학교만
                ]
            }
            
            output_file = Path(__file__).parent.parent / "data" / "schools_initial.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schools_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {len(schools_data['schools'])}개 학교를 {output_file}에 저장했습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    export_schools_to_json()
