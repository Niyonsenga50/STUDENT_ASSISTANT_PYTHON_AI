
import numpy as np

from services.document_processor import load_pdf_documents
from services.text_splitter import split_text
from services.embeddings import create_embedding, create_embeddings


MIN_SIMILARITY = 0.45


def build_knowledge_base():

    documents = load_pdf_documents()

    knowledge_base = []

    for document in documents:

        chunks = split_text(document["text"])

        for chunk in chunks:

            knowledge_base.append(
                {
                    "filename": document["filename"],
                    "content": chunk
                }
            )

    contents = [
        item["content"]
        for item in knowledge_base
    ]

    if contents:

        embeddings = create_embeddings(contents)

        for item, embedding in zip(
            knowledge_base,
            embeddings
        ):

            item["embedding"] = embedding

    return knowledge_base


def search_knowledge(
    question,
    knowledge_base,
    max_results=3
):

    if not knowledge_base:
        return []

    question_embedding = create_embedding(question)

    results = []

    for item in knowledge_base:

        similarity = np.dot(
            item["embedding"],
            question_embedding
        )

        if similarity >= MIN_SIMILARITY:

            results.append(
                {
                    "filename": item["filename"],
                    "content": item["content"],
                    "score": float(similarity)
                }
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:max_results]

