# utils/utils.py
import os
import random
import fitz 
import docx
from config import SYSTEM_PAGE_LIMIT

def extract_text_from_file(file, MAX_PAGE_LIMIT=SYSTEM_PAGE_LIMIT):
    # ✅ Use this instead to get a name or default value
    filename = getattr(file, 'filename', 'uploaded_file')

    ext = os.path.splitext(filename)[1].lower()
    text = ""
    page_count = 0
    selected_indexes = []  # <-- New: to track selected page numbers or chunk indexes

    if ext == '.pdf':
        try:
            pdf_doc = fitz.open(stream=file.read(), filetype="pdf")
            page_data = []

            for i, page in enumerate(pdf_doc.pages()):
                page_text = page.get_text() or ""
                word_count = len(page_text.split())
                page_data.append({
                    "page_number": i + 1,  # 1-based page numbering
                    "text": page_text.strip(),
                    "word_count": word_count
                })

            if page_data:
                sorted_pages = sorted(page_data, key=lambda x: x['word_count'], reverse=True)
                top_rich_pages = sorted_pages[:max(1, int(len(sorted_pages) * 0.7))]
                selected_pages = random.sample(top_rich_pages, min(MAX_PAGE_LIMIT, len(top_rich_pages)))

                text = "\n".join([page['text'] for page in selected_pages])
                selected_indexes = [page['page_number'] for page in selected_pages]
                page_count = len(selected_pages)

        except Exception as e:
            print(f"[fitz PDF ERROR] {e}")

    elif ext == '.docx':
        try:
            doc = docx.Document(file)
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            chunks = []
            current_chunk = ""
            for para in paragraphs:
                current_chunk += " " + para
                if len(current_chunk.split()) >= 300:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
            if current_chunk:
                chunks.append(current_chunk.strip())

            if chunks:
                selected_chunks = random.sample(chunks, min(MAX_PAGE_LIMIT, len(chunks)))
                text = "\n".join(selected_chunks)
                selected_indexes = [chunks.index(chunk) + 1 for chunk in selected_chunks]  # 1-based chunk numbers
                page_count = len(selected_chunks)

        except Exception as e:
            print(f"[DOCX ERROR] {e}")

    elif ext == '.txt':
        try:
            text = file.read().decode('utf-8')
            page_count = 1
            selected_indexes = [1]
        except Exception as e:
            print(f"[TXT ERROR] {e}")

    if len(text.strip()) < 20 and ext in ('.pdf', '.docx'):
        text = ""
        page_count = 0
        selected_indexes = []

    print(f"[DEBUG] File extension: {ext}")
    print(f"[DEBUG] Extracted text length: {len(text)} characters")
    print(f"[DEBUG] Extracted page count: {page_count}")
    print(f"[DEBUG] Selected page/chunk indexes: {selected_indexes}")


    return text, len(text), selected_indexes
