from services.document_processor import load_pdf_documents


documents = load_pdf_documents()

print("Documents found:", len(documents))

for document in documents:

    print("--------------------------------")
    print("File:", document["filename"])
    print("Pages:", document["pages"])
    print("Characters:", len(document["text"]))