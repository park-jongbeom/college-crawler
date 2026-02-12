"""
GraphRAG Seed Data 삽입 스크립트.

Phase 1 Week 2: 10개 학교에 대한 검증용 Knowledge Graph Triples를 DB에 삽입합니다.

사용법:
    python scripts/seed_graphrag_data.py

환경변수:
    DATABASE_HOST: PostgreSQL 호스트
    DATABASE_PORT: PostgreSQL 포트 (기본값: 5432)
    DATABASE_NAME: 데이터베이스명
    DATABASE_USER: 사용자명
    DATABASE_PASSWORD: 비밀번호
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import SimpleConnectionPool

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphRAGSeedDataLoader:
    """GraphRAG Seed Data를 PostgreSQL에 삽입하는 클래스."""

    def __init__(self) -> None:
        """데이터베이스 연결 초기화."""
        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "port": int(os.getenv("DATABASE_PORT", "5432")),
            "database": os.getenv("DATABASE_NAME"),
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
        }

        if not all(self.db_config.values()):
            raise ValueError("데이터베이스 환경변수가 설정되지 않았습니다.")

        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            **self.db_config,
        )

    def load_seed_data(self, json_path: str | Path) -> None:
        """
        Seed Data JSON 파일을 읽어서 DB에 삽입합니다.

        Args:
            json_path: Seed Data JSON 파일 경로
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Seed Data 파일을 찾을 수 없습니다: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        schools_data = data.get("schools", [])
        logger.info(f"총 {len(schools_data)}개 학교의 Seed Data를 로드합니다.")

        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # 트랜잭션 시작
                conn.autocommit = False

                entity_map: dict[str, UUID] = {}  # entity_name -> uuid 매핑

                for school_data in schools_data:
                    school_name = school_data["school_name"]
                    triples = school_data["triples"]

                    logger.info(f"처리 중: {school_name} ({len(triples)}개 Triples)")

                    # 1. School Entity 생성/조회
                    school_uuid = self._ensure_entity(
                        cur=cur,
                        entity_type="School",
                        entity_name=school_name,
                        canonical_name=school_name,
                        entity_map=entity_map,
                    )

                    # 2. 모든 Triples의 Head/Tail Entity 생성
                    for triple in triples:
                        head_name = triple["head"]
                        tail_name = triple["tail"]

                        # Head Entity 생성
                        head_uuid = self._ensure_entity(
                            cur=cur,
                            entity_type=self._infer_entity_type(head_name, school_name),
                            entity_name=head_name,
                            canonical_name=head_name,
                            entity_map=entity_map,
                            school_id=school_uuid if head_name == school_name else None,
                        )

                        # Tail Entity 생성
                        tail_uuid = self._ensure_entity(
                            cur=cur,
                            entity_type=self._infer_entity_type(tail_name, school_name),
                            entity_name=tail_name,
                            canonical_name=tail_name,
                            entity_map=entity_map,
                        )

                    # 3. Triples 삽입
                    self._insert_triples(
                        cur=cur,
                        triples=triples,
                        entity_map=entity_map,
                        source_url=None,
                    )

                # 커밋
                conn.commit()
                logger.info("✅ 모든 Seed Data 삽입 완료")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Seed Data 삽입 실패: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def _ensure_entity(
        self,
        cur: Any,
        entity_type: str,
        entity_name: str,
        canonical_name: str,
        entity_map: dict[str, UUID],
        school_id: UUID | None = None,
    ) -> UUID:
        """
        Entity가 존재하면 UUID를 반환하고, 없으면 생성합니다.

        Args:
            cur: 데이터베이스 커서
            entity_type: Entity 타입
            entity_name: Entity 이름
            canonical_name: 정규화된 이름
            entity_map: Entity 이름 -> UUID 매핑 캐시
            school_id: School Entity의 경우 school_id

        Returns:
            Entity UUID
        """
        # 캐시 확인
        cache_key = f"{entity_type}:{canonical_name}"
        if cache_key in entity_map:
            return entity_map[cache_key]

        # DB에서 조회
        cur.execute(
            """
            SELECT uuid FROM entities
            WHERE entity_type = %s AND canonical_name = %s
            """,
            (entity_type, canonical_name),
        )
        row = cur.fetchone()

        if row:
            uuid_val = row[0]
        else:
            # 새 Entity 생성
            uuid_val = uuid4()
            cur.execute(
                """
                INSERT INTO entities (
                    uuid, entity_type, entity_name, canonical_name,
                    school_id, confidence_score, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (uuid_val, entity_type, entity_name, canonical_name, school_id, 1.0),
            )

        entity_map[cache_key] = uuid_val
        return uuid_val

    def _infer_entity_type(self, entity_name: str, school_name: str) -> str:
        """
        Entity 이름으로부터 타입을 추론합니다.

        Args:
            entity_name: Entity 이름
            school_name: 학교명 (컨텍스트)

        Returns:
            Entity 타입
        """
        if entity_name == school_name:
            return "School"

        # 간단한 휴리스틱 (실제로는 더 정교한 로직 필요)
        known_companies = ["Google", "Microsoft", "Amazon", "Tesla", "Meta", "Apple"]
        known_jobs = ["Software Engineer", "AI Engineer", "Data Scientist", "Product Manager", "Robotics Engineer"]
        known_skills = ["Machine Learning", "Deep Learning", "Python", "Algorithms", "Robotics", "Statistics"]
        known_programs = ["Computer Science", "Data Science", "Business Administration", "Electrical Engineering", "Mechanical Engineering", "Software Engineering", "Robotics", "Artificial Intelligence", "Automotive Technology"]

        if entity_name in known_companies:
            return "Company"
        elif entity_name in known_jobs:
            return "Job"
        elif entity_name in known_skills:
            return "Skill"
        elif entity_name in known_programs:
            return "Program"
        elif "," in entity_name and any(state in entity_name for state in ["California", "Massachusetts", "New York", "Pennsylvania"]):
            return "Location"
        else:
            # 기본값: Program (가장 일반적)
            return "Program"

    def _insert_triples(
        self,
        cur: Any,
        triples: list[dict[str, Any]],
        entity_map: dict[str, UUID],
        source_url: str | None = None,
    ) -> None:
        """
        Triples를 knowledge_triples 테이블에 삽입합니다.

        Args:
            cur: 데이터베이스 커서
            triples: Triple 리스트
            entity_map: Entity 이름 -> UUID 매핑
            source_url: 출처 URL
        """
        triple_rows = []
        for triple in triples:
            head_name = triple["head"]
            tail_name = triple["tail"]
            relation = triple["relation"]
            confidence = float(triple.get("confidence", 0.8))

            # Entity UUID 조회
            head_type = self._infer_entity_type(head_name, "")
            tail_type = self._infer_entity_type(tail_name, "")
            head_key = f"{head_type}:{head_name}"
            tail_key = f"{tail_type}:{tail_name}"

            head_uuid = entity_map.get(head_key)
            tail_uuid = entity_map.get(tail_key)

            if not head_uuid or not tail_uuid:
                logger.warning(f"Entity를 찾을 수 없습니다: {head_name} 또는 {tail_name}")
                continue

            triple_rows.append((
                uuid4(),  # id
                head_uuid,  # head_entity_uuid
                head_type,  # head_entity_type
                head_name,  # head_entity_name
                relation,  # relation_type
                tail_uuid,  # tail_entity_uuid
                tail_type,  # tail_entity_type
                tail_name,  # tail_entity_name
                1.0,  # weight
                confidence,  # confidence_score
                "{}",  # properties (JSONB)
                source_url,  # source_url
                "manual",  # source_type
                "seed_data",  # extraction_method
            ))

        if triple_rows:
            execute_values(
                cur,
                """
                INSERT INTO knowledge_triples (
                    id, head_entity_uuid, head_entity_type, head_entity_name,
                    relation_type,
                    tail_entity_uuid, tail_entity_type, tail_entity_name,
                    weight, confidence_score, properties,
                    source_url, source_type, extraction_method,
                    created_at, updated_at
                ) VALUES %s
                """,
                triple_rows,
                template="""
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, NOW(), NOW())
                """,
            )
            logger.info(f"  → {len(triple_rows)}개 Triples 삽입 완료")

    def close(self) -> None:
        """연결 풀 종료."""
        if self.pool:
            self.pool.closeall()


def main() -> None:
    """메인 함수."""
    seed_data_path = project_root / "data" / "seed_triples.json"

    loader = GraphRAGSeedDataLoader()
    try:
        loader.load_seed_data(seed_data_path)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
