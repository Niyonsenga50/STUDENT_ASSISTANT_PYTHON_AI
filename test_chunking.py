from services.document_processor import load_pdf_documents
from services.text_splitter import split_text


documents = load_pdf_documents()

for document in documents:

    chunks = split_text(document["text"])

    print("--------------------------------")
    print("File:", document["filename"])
    print("Pages:", document["pages"])
    print("Chunks:", len(chunks))

    if chunks:
        print("First chunk:")
        print(chunks[0][:500])