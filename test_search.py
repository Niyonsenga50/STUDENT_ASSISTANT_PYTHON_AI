from search import search_documents


documents = [
    "A database is an organised collection of data.",
    "A primary key uniquely identifies each record in a database.",
    "HTML is a markup language used to structure web pages.",
    "A computer network allows computers to communicate with each other."
]


question = "What identifies a record in a database?"


results = search_documents(
    question,
    documents,
    top_k=2
)


print("\nSearch results:\n")

for result in results:
    print("Score:", result["score"])
    print("Text:", result["text"])
    print("-" * 50)