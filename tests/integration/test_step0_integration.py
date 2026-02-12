import pytest

from src.crawlers.chunking import SemanticChunker
from src.services.entity_resolution import EntityResolver
from src.services.prompt_templates import extract_triples_rule_based


@pytest.mark.integration
def test_step0_pipeline_html_to_normalized_triples():
    html = """
    <html>
      <body>
        <section>
          Stanford's Computer Science program teaches Machine Learning and Python.
          Graduates work at Google and Microsoft.
        </section>
        <section>
          The school is located in Palo Alto, California.
          The program prepares students for careers as Data Scientist.
        </section>
      </body>
    </html>
    """

    chunker = SemanticChunker()
    resolver = EntityResolver()

    chunks = chunker.chunk_html(html, chunk_size=160, overlap=32)
    assert chunks, "청킹 결과가 비어 있으면 안 됩니다."

    extracted = []
    for chunk in chunks:
        extracted.extend(extract_triples_rule_based(chunk.text, school_name="Stanford"))

    normalized = resolver.normalize_triples(extracted)
    assert normalized, "정규화 결과가 비어 있으면 안 됩니다."

    # 핵심 관계 최소 커버리지 검증
    relations = {triple.relation for triple in normalized}
    assert "OFFERS" in relations
    assert "DEVELOPS" in relations
    assert "HIRES_FROM" in relations

    # confidence 품질 기준 검증
    assert all(triple.confidence >= 0.8 for triple in normalized)
