import PyPDF2
import google.generativeai as genai
from PIL import Image
import pytesseract
import pdf2image

import numpy as np
import os

# 🔥 NEW IMPORTS
from sentence_transformers import SentenceTransformer
import faiss

# 🔑 Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔑 Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Models
model = genai.GenerativeModel("models/gemini-2.5-flash")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')


# ===========================
# 📄 TEXT EXTRACTION
# ===========================
def extract_text_from_pdf(file):
    text = ""

    try:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content

        # OCR fallback
        if len(text.strip()) < 50:
            file.seek(0)

            images = pdf2image.convert_from_bytes(
                file.read(),
                poppler_path=r"C:\Users\rajan\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
            )

            for img in images:
                img_np = np.array(img)
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text
                
                
                # gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
                # blur = cv2.GaussianBlur(gray, (5, 5), 0)

                thresh = cv2.adaptiveThreshold(
                    blur, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )

                thresh = cv2.bitwise_not(thresh)

                ocr_text = pytesseract.image_to_string(
                    thresh, config='--oem 3 --psm 6'
                )

                if len(ocr_text.strip()) > 10:
                    text += ocr_text

        return text.strip()

    except Exception as e:
        print("Error:", e)
        return ""


# ===========================
# 🧹 CLEAN TEXT
# ===========================
def clean_text(text):
    lines = text.split("\n")
    return "\n".join([l.strip() for l in lines if len(l.strip()) > 3])


# ===========================
# 📝 SUMMARY
# ===========================
def summarize_text(text):
    text = clean_text(text)

    prompt = f"""
    Summarize into bullet points and simple language:

    {text[:3000]}
    """

    return model.generate_content(prompt).text


# ===========================
# ❓ QUESTIONS
# ===========================
def generate_questions(text):
    text = clean_text(text)

    prompt = f"""
    Generate 5 important exam questions:

    {text[:3000]}
    """

    return model.generate_content(prompt).text


# ===========================
# 🔥 TRUE RAG (FAISS)
# ===========================

def create_vector_store(text):
    chunks = text.split("\n")
    chunks = [c for c in chunks if len(c.strip()) > 20]

    # 🚨 HANDLE EMPTY TEXT
    if len(chunks) == 0:
        return [], None

    embeddings = embed_model.encode(chunks)

    # 🚨 HANDLE EMPTY EMBEDDINGS
    if len(embeddings) == 0:
        return [], None

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings))

    return chunks, index


def search_chunks(query, chunks, index, k=3):
    query_embedding = embed_model.encode([query])

    distances, indices = index.search(np.array(query_embedding), k)

    return [chunks[i] for i in indices[0]]


def smart_ask(chunks, index, question):
    relevant_chunks = search_chunks(question, chunks, index)

    context = "\n".join(relevant_chunks)

    prompt = f"""
    You are an intelligent study assistant.

    Answer clearly using the context below.
    If multiple topics are involved, connect them logically.

    Context:
    {context}

    Question:
    {question}
    """

    response = model.generate_content(prompt)

    return response.text, relevant_chunks
