#!/usr/bin/env python3
"""
모니터링 서버 실행 스크립트
"""

import uvicorn
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "src.monitor.api:app",
        host="0.0.0.0",
        port=8080,
        reload=False,  # 운영 환경에서는 reload 비활성화
        log_level="info"
    )
