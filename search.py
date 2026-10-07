import numpy as np

from embeddings import create_embedding, create_embeddings


def cosine_similarity(query_embedding, document_embeddings):
    """
    Calculate similarity between the question
    and document embeddings.
    """

    return np.dot(
        document_embeddings,
        query_embedding
    )


def search_documents(query, documents, top_k=3):
    """
    Find the most relevant document chunks
    for a user's question.
    """

    query_embedding = create_embedding(query)

    document_embeddings = create_embeddings(documents)

    similarities = cosine_similarity(
        query_embedding,
        document_embeddings
    )

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for index in top_indices:
        results.append({
            "content": documents[index],
            "score": float(similarities[index])
        })

    return results