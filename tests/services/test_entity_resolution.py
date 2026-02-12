import pytest

from src.services.entity_resolution import EntityResolver
from src.services.prompt_templates import Triple


@pytest.mark.unit
def test_entity_resolver_alias_mapping():
    resolver = EntityResolver()

    assert resolver.normalize("MIT", "School") == "Massachusetts Institute of Technology"
    assert resolver.normalize("ML", "Skill") == "Machine Learning"
    assert resolver.normalize("Google LLC", "Company") == "Google"


@pytest.mark.unit
def test_entity_resolver_relation_normalization():
    resolver = EntityResolver()

    assert resolver.normalize_relation("offers") == "OFFERS"
    assert resolver.normalize_relation("leads-to") == "LEADS_TO"
    assert resolver.normalize_relation("unknown_link") == "RELATED_TO"


@pytest.mark.unit
def test_entity_resolver_normalize_triples_deduplicates():
    resolver = EntityResolver()
    triples = [
        Triple(head="MIT", relation="offers", tail="CS", confidence=0.95),
        Triple(head="Massachusetts Institute of Technology", relation="OFFERS", tail="Computer Science", confidence=0.94),
    ]

    normalized = resolver.normalize_triples(triples)
    assert len(normalized) == 1
    assert normalized[0].head == "Massachusetts Institute of Technology"
    assert normalized[0].tail == "Computer Science"
