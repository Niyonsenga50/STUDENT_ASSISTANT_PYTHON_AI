from embeddings import create_embedding, create_embeddings

text = "What is a database?"

embedding = create_embedding(text)

print("Embedding created successfully!")
print("Number of values:", len(embedding))
print("First 5 values:", embedding[:5])


texts = [
    "A database stores organised data.",
    "A primary key uniquely identifies a record.",
    "HTML is used to create web pages."
]

embeddings = create_embeddings(texts)

print("Number of texts:", len(embeddings))
print("Size of each embedding:", len(embeddings[0]))