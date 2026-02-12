"""
Semantic Chunking 유틸.

참고 자료:
- https://github.com/microsoft/graphrag
- https://github.com/run-llama/llama_index
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup


_SPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    """청크 결과 모델."""

    text: str
    start_pos: int
    end_pos: int


class SemanticChunker:
    """HTML을 의미 단위로 분할하고 오버랩을 보존합니다."""

    def chunk_html(self, html: str, chunk_size: int = 1000, overlap: int = 200) -> list[Chunk]:
        """
        HTML을 의미 단위 텍스트로 변환한 뒤 청킹합니다.

        Args:
            html: 원본 HTML
            chunk_size: 청크 최대 길이(문자 수)
            overlap: 다음 청크에 재사용할 오버랩 길이(문자 수)
        """
        self._validate_sizes(chunk_size=chunk_size, overlap=overlap)
        if not html or not html.strip():
            return []

        sections = self._extract_sections(html)
        if not sections:
            return []
        normalized = "\n".join(sections)
        return self.chunk_text(normalized, chunk_size=chunk_size, overlap=overlap)

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[Chunk]:
        """정규화된 plain text를 의미 단위로 청킹합니다."""
        self._validate_sizes(chunk_size=chunk_size, overlap=overlap)
        if not text or not text.strip():
            return []

        normalized = _SPACE_RE.sub(" ", text).strip()
        if len(normalized) <= chunk_size:
            return [Chunk(text=normalized, start_pos=0, end_pos=len(normalized))]

        sentences = self._split_sentences(normalized)
        return self._build_chunks(sentences=sentences, chunk_size=chunk_size, overlap=overlap)

    @staticmethod
    def _validate_sizes(chunk_size: int, overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size는 0보다 커야 합니다.")
        if overlap < 0:
            raise ValueError("overlap은 음수가 될 수 없습니다.")
        if overlap >= chunk_size:
            raise ValueError("overlap은 chunk_size보다 작아야 합니다.")

    @staticmethod
    def _extract_sections(html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        sections: list[str] = []
        candidates = soup.find_all(["section", "article", "div", "p", "li"])

        for tag in candidates:
            text = tag.get_text(" ", strip=True)
            text = _SPACE_RE.sub(" ", text).strip()
            if len(text) >= 40:
                sections.append(text)

        if sections:
            return sections

        fallback = soup.get_text(" ", strip=True)
        fallback = _SPACE_RE.sub(" ", fallback).strip()
        return [fallback] if fallback else []

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        parts = [part.strip() for part in _SENTENCE_SPLIT_RE.split(text) if part.strip()]
        if parts:
            return parts
        return [text]

    def _build_chunks(self, sentences: Iterable[str], chunk_size: int, overlap: int) -> list[Chunk]:
        chunks: list[Chunk] = []
        current = ""
        cursor = 0

        def flush(chunk_text: str) -> None:
            nonlocal cursor
            chunk_text = chunk_text.strip()
            if not chunk_text:
                return
            start = cursor
            end = start + len(chunk_text)
            chunks.append(Chunk(text=chunk_text, start_pos=start, end_pos=end))
            cursor = max(0, end - overlap)

        for sentence in sentences:
            candidate = sentence if not current else f"{current} {sentence}"
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            if current:
                flush(current)
                overlap_text = current[-overlap:].strip() if overlap > 0 else ""
                current = f"{overlap_text} {sentence}".strip() if overlap_text else sentence
            else:
                # 문장이 chunk_size보다 길면 강제로 자릅니다.
                slices = self._slice_long_sentence(sentence, chunk_size=chunk_size, overlap=overlap)
                for piece in slices[:-1]:
                    flush(piece)
                current = slices[-1] if slices else ""

            while len(current) > chunk_size:
                pieces = self._slice_long_sentence(current, chunk_size=chunk_size, overlap=overlap)
                for piece in pieces[:-1]:
                    flush(piece)
                current = pieces[-1]

        if current:
            flush(current)

        return chunks

    @staticmethod
    def _slice_long_sentence(sentence: str, chunk_size: int, overlap: int) -> list[str]:
        pieces: list[str] = []
        text = sentence.strip()
        if not text:
            return pieces

        step = chunk_size - overlap if overlap > 0 else chunk_size
        if step <= 0:
            step = chunk_size

        index = 0
        while index < len(text):
            piece = text[index : index + chunk_size].strip()
            if piece:
                pieces.append(piece)
            index += step
        return pieces
