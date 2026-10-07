from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


model = SentenceTransformer(MODEL_NAME)


def create_embedding(text):
    """
    Convert text into a Deep Learning embedding.
    """
    return model.encode(
        text,
        normalize_embeddings=True
    )


def create_embeddings(texts):
    """
    Convert multiple texts into Deep Learning embeddings.
    """
    return model.encode(
        texts,
        normalize_embeddings=True
    )