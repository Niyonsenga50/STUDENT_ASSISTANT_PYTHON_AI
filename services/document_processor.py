from pathlib import Path
from pypdf import PdfReader


RESOURCES_FOLDER = Path("resources")


def load_pdf_documents():
    """
    Read all PDF documents from the resources folder.

    Returns:
        A list containing document information and extracted text.
    """

    documents = []

    pdf_files = list(RESOURCES_FOLDER.glob("*.pdf"))

    for pdf_file in pdf_files:

        reader = PdfReader(str(pdf_file))

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        documents.append(
            {
                "filename": pdf_file.name,
                "pages": len(reader.pages),
                "text": text
            }
        )

    return documents