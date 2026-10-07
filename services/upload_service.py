"""
Handles user-uploaded documents: extract -> clean -> chunk -> embed -> search -> answer.

Result dicts use the same keys as your existing search_service
(score, filename, content) plus "page", so the UI can treat both the same.

pip install pypdf python-docx sentence-transformers numpy anthropic
"""

import io
import os
import re

import numpy as np
import streamlit as st
from pypdf import PdfReader

EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_CHARS = 900
OVERLAP_SENTENCES = 2
MIN_SCORE = 0.25  # below this the question is treated as "not in the document"


# ---------------------------------------------------------------- loading ---
def _clean(text: str) -> str:
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)             # fix hyphenation
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.M)   # lone page numbers
    text = re.sub(r"\s*\n\s*", " ", text)                     # join broken lines
    return re.sub(r"\s{2,}", " ", text).strip()


def _sections(text: str, size: int = 3000):
    text = _clean(text)
    return [(f"Section {i + 1}", text[s:s + size])
            for i, s in enumerate(range(0, len(text), size))]


def _load_pages(uploaded):
    name = uploaded.name.lower()
    data = uploaded.getvalue()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        pages = [(f"Page {i}", _clean(p.extract_text() or ""))
                 for i, p in enumerate(reader.pages, 1)]
    elif name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        pages = _sections("\n".join(p.text for p in doc.paragraphs))
    else:
        pages = _sections(data.decode("utf-8", errors="ignore"))

    return [(label, text) for label, text in pages if text]


def _chunk(pages, filename):
    chunks = []
    for label, text in pages:
        buf: list[str] = []
        for sent in re.split(r"(?<=[.!?])\s+", text):
            buf.append(sent)
            if sum(len(s) for s in buf) >= CHUNK_CHARS:
                chunks.append({"filename": filename, "page": label,
                               "content": " ".join(buf)})
                buf = buf[-OVERLAP_SENTENCES:]
        if buf and (not chunks or " ".join(buf) not in chunks[-1]["content"]):
            chunks.append({"filename": filename, "page": label,
                           "content": " ".join(buf)})
    return chunks


# ------------------------------------------------------------- embeddings ---
@st.cache_resource(show_spinner="Loading embedding model...")
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


def build_index_from_upload(uploaded):
    """Returns {"chunks", "vecs", "pages"} or None if no text could be read."""
    pages = _load_pages(uploaded)
    if not pages:
        return None
    chunks = _chunk(pages, uploaded.name)
    vecs = _model().encode([c["content"] for c in chunks],
                           normalize_embeddings=True, show_progress_bar=False)
    return {"chunks": chunks, "vecs": np.asarray(vecs), "pages": len(pages)}


def search_upload(question, index, max_results=4):
    q = _model().encode([question], normalize_embeddings=True)[0]
    scores = index["vecs"] @ q
    top = np.argsort(scores)[::-1][:max_results]
    return [{**index["chunks"][i], "score": float(scores[i])} for i in top]


# ------------------------------------------------------------- generation ---
def _llm_answer(question, results):
    import anthropic
    context = "\n\n".join(
        f"[{i}] ({r.get('page') or r.get('filename', 'source')}) {r['content']}"
        for i, r in enumerate(results, 1))
    prompt = (
        "Answer the question using ONLY the numbered excerpts below. "
        "Write a clear, well-organised answer in your own words and cite "
        "sources inline like [1] or [2]. If the excerpts don't contain the "
        "answer, say the document doesn't cover it.\n\n"
        f"Excerpts:\n{context}\n\nQuestion: {question}"
    )
    resp = anthropic.Anthropic().messages.create(
        model="claude-sonnet-5-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _extractive_answer(question, results):
    """No-LLM fallback: best-matching sentences from the retrieved chunks."""
    cands = [(i, s) for i, r in enumerate(results, 1)
             for s in re.split(r"(?<=[.!?])\s+", r["content"]) if len(s) > 40]
    if not cands:
        return results[0]["content"]
    m = _model()
    vecs = m.encode([s for _, s in cands], normalize_embeddings=True)
    q = m.encode([question], normalize_embeddings=True)[0]
    best = sorted(np.argsort(vecs @ q)[::-1][:3])
    return "\n\n".join(f"{cands[j][1]} [{cands[j][0]}]" for j in best)


def answer_from_upload(question, results, apply_threshold=True):
    """Returns (answer_text, references_used).

    apply_threshold=False skips the MIN_SCORE check; use it when the results
    come from a retriever whose scores aren't cosine similarities.
    """
    if not results:
        return ("I couldn't find anything in the document that "
                "answers this question.", [])
    if apply_threshold and results[0]["score"] < MIN_SCORE:
        return ("I couldn't find anything in the uploaded document that "
                "answers this question.", [])
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return _llm_answer(question, results), results
        except Exception as e:
            st.warning(f"LLM call failed ({e}); showing extracted sentences.")
    return _extractive_answer(question, results), results
