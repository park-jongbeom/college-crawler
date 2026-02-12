"""
TripleExtractionService 테스트.

참고: 실제 Gemini API 호출은 mock으로 처리합니다.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.entity_resolution import NormalizedTriple
from src.services.prompt_templates import Triple
from src.services.triple_extraction_service import TripleExtractionService


@pytest.fixture
def mock_gemini_response():
    """Gemini API 응답 Mock."""
    response = MagicMock()
    response.text = json.dumps({
        "triples": [
            {
                "head": "Stanford University",
                "relation": "OFFERS",
                "tail": "Computer Science",
                "confidence": 0.95
            },
            {
                "head": "Computer Science",
                "relation": "DEVELOPS",
                "tail": "Machine Learning",
                "confidence": 0.93
            },
            {
                "head": "Google",
                "relation": "HIRES_FROM",
                "tail": "Stanford University",
                "confidence": 0.91
            }
        ]
    })
    return response


@pytest.fixture
def sample_html():
    """테스트용 HTML 샘플."""
    return """
    <html>
        <body>
            <section>
                <h1>Stanford University</h1>
                <p>Stanford's Computer Science program teaches Machine Learning and graduates work at Google.</p>
            </section>
        </body>
    </html>
    """


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_triple_extraction_service_initialization(mock_genai):
    """TripleExtractionService 초기화 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key")

    assert service.api_key == "test-key"
    assert service.confidence_threshold == 0.8
    mock_genai.configure.assert_called_once_with(api_key="test-key")


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_extract_from_html_success(mock_genai, sample_html, mock_gemini_response):
    """HTML에서 Triples 추출 성공 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_gemini_response
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key", confidence_threshold=0.8)

    result = service.extract_from_html(
        html=sample_html,
        school_name="Stanford University",
        source_url="https://example.com"
    )

    assert len(result) >= 3
    assert all(isinstance(t, NormalizedTriple) for t in result)
    assert all(t.confidence >= 0.8 for t in result)

    # 정규화 확인
    head_names = [t.head for t in result]
    assert any("Stanford" in name for name in head_names)


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_extract_from_html_empty_html(mock_genai):
    """빈 HTML 처리 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key")

    result = service.extract_from_html(html="", school_name="Test School")

    assert result == []


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_extract_from_html_confidence_filtering(mock_genai, sample_html):
    """Confidence 필터링 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    
    # 낮은 confidence를 포함한 응답
    low_confidence_response = MagicMock()
    low_confidence_response.text = json.dumps({
        "triples": [
            {"head": "A", "relation": "OFFERS", "tail": "B", "confidence": 0.95},
            {"head": "C", "relation": "DEVELOPS", "tail": "D", "confidence": 0.5},  # 낮은 confidence
        ]
    })
    mock_model.generate_content.return_value = low_confidence_response
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key", confidence_threshold=0.8)

    result = service.extract_from_html(html=sample_html)

    # confidence >= 0.8인 것만 반환되어야 함
    assert len(result) == 1
    assert result[0].confidence >= 0.8


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_parse_response_json_code_block(mock_genai):
    """JSON 코드 블록이 포함된 응답 파싱 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    
    response_with_code_block = MagicMock()
    response_with_code_block.text = "```json\n" + json.dumps({
        "triples": [
            {"head": "A", "relation": "OFFERS", "tail": "B", "confidence": 0.9}
        ]
    }) + "\n```"
    mock_model.generate_content.return_value = response_with_code_block
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key")
    
    result = service._extract_from_chunk("Test text")

    assert len(result) == 1
    assert result[0].head == "A"
    assert result[0].relation == "OFFERS"


@pytest.mark.unit
@patch("src.services.triple_extraction_service.genai")
def test_extract_from_html_api_error_handling(mock_genai, sample_html):
    """API 에러 처리 테스트."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API Error")
    mock_genai.GenerativeModel.return_value = mock_model

    service = TripleExtractionService(api_key="test-key")

    # 에러 발생 시 빈 리스트 반환
    result = service.extract_from_html(html=sample_html)

    assert result == []


@pytest.mark.unit
def test_parse_response_invalid_json():
    """잘못된 JSON 응답 처리 테스트."""
    service = TripleExtractionService(api_key="test-key")

    result = service._parse_response("Invalid JSON {")

    assert result == []


@pytest.mark.integration
@pytest.mark.skip(reason="실제 Gemini API 호출 테스트는 수동 실행")
def test_extract_from_html_real_api():
    """실제 Gemini API 호출 통합 테스트 (수동 실행용)."""
    import os
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    service = TripleExtractionService(api_key=api_key)

    html = """
    <section>
        Stanford's Computer Science program teaches Machine Learning.
        Graduates work at Google and Microsoft.
    </section>
    """

    result = service.extract_from_html(
        html=html,
        school_name="Stanford University"
    )

    assert len(result) >= 3
    assert any(t.relation == "OFFERS" for t in result)
    assert any(t.relation == "DEVELOPS" for t in result)
    assert all(t.confidence >= 0.8 for t in result)
