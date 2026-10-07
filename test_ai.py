from services.search_service import (
    build_knowledge_base,
    search_knowledge
)

from services.ai_service import generate_answer


knowledge_base = build_knowledge_base()

question = input("Ask a question: ")

results = search_knowledge(
    question,
    knowledge_base,
    max_results=3
)

answer = generate_answer(
    question,
    results
)

print("\nAI ANSWER")
print("==============================")

print(answer)