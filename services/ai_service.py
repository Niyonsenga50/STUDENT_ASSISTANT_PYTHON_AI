"""
Answer generation for the built-in course materials.

Every answer is now produced from the retrieved chunks. There are no
hardcoded replies and no raw-chunk fallback.
"""

from services.upload_service import answer_from_upload


def generate_answer(question, search_results):

    if not search_results:
        return (
            "I could not find relevant information "
            "in the available course materials."
        )

    # apply_threshold=False because search_knowledge may use a different
    # score scale than cosine similarity. Set it to True if your scores are
    # cosine similarities between 0 and 1.
    answer, _ = answer_from_upload(
        question,
        search_results,
        apply_threshold=False
    )

    return answer
