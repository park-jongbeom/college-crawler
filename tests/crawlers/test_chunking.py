import pytest

from src.crawlers.chunking import SemanticChunker


@pytest.mark.unit
def test_chunk_html_keeps_overlap_context():
    chunker = SemanticChunker()
    html = """
    <html><body>
      <section>
        Stanford University Computer Science program teaches Machine Learning.
        Graduates work at Google and Microsoft in Silicon Valley.
        The curriculum focuses on Python, Algorithms, and Cloud Computing.
      </section>
      <section>
        Students also receive project-based training with industry mentors.
      </section>
    </body></html>
    """

    chunks = chunker.chunk_html(html, chunk_size=120, overlap=30)

    assert len(chunks) >= 2
    assert chunks[0].text[-20:].strip()
    assert chunks[1].text[:30].strip()


@pytest.mark.unit
def test_chunk_text_respects_max_chunk_size():
    chunker = SemanticChunker()
    text = " ".join(["Sentence about program and career outcomes."] * 50)
    chunks = chunker.chunk_text(text, chunk_size=160, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 160 for chunk in chunks)


@pytest.mark.unit
def test_chunk_text_raises_on_invalid_size_arguments():
    chunker = SemanticChunker()
    with pytest.raises(ValueError):
        chunker.chunk_text("hello", chunk_size=100, overlap=100)
