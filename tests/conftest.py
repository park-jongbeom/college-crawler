"""
pytest 설정 및 공통 fixture
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
