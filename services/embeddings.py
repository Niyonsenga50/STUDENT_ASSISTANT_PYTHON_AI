
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def create_embedding(text):
    return model.encode(
        text,
        normalize_embeddings=True
    )


def create_embeddings(texts):
    return model.encode(
        texts,
        normalize_embeddings=True
    )

