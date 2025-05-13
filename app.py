import streamlit as st
import os
import requests
import PyPDF2
import re
from PIL import Image
import pytesseract

# Streamlit App Title
st.title("QuantumQuery (Powered by Grok)")
st.write("Ask me anything about Quantum Physics! Optionally, upload a PDF or image for extra context.")

# User inputs
user_question = st.text_input("Your question:")

# API key handling
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    api_key = st.text_input("Enter your Groq API Key:", type="password")

# Constants
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

# Simple summarizer using regex (no nltk)
def summarize_text(text, num_sentences=5):
    sentences = re.split(r'(?<=[.!?]) +', text)
    summary = sentences[:num_sentences]
    return " ".join(summary)

# PDF Extractor + Summarizer
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    pdf_text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            pdf_text += page_text
    if pdf_text.strip():
        return summarize_text(pdf_text, num_sentences=5)
    else:
        return ""

# Image Extractor + Summarizer
def extract_text_from_image(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        if text.strip():
            return summarize_text(text, num_sentences=5)
        else:
            return ""
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

# Clean and display Groq reply
def clean_and_display_grok_reply(reply):
    reply = re.sub(
        r'\$\$(.*?)\$\$\s*\$\$(.*?)\$\$\s*\$\$(.*?)\$\$',
        r'$$\1 \2 \3$$',
        reply,
        flags=re.DOTALL
    )
    reply = re.sub(
        r'\$\$(.*?)\$\$\s*\$\$(.*?)\$\$',
        r'$$\1 \2$$',
        reply,
        flags=re.DOTALL
    )
    st.markdown(reply, unsafe_allow_html=True)

# Upload PDF
uploaded_file = st.file_uploader(
    "Upload a PDF (optional):",
    type=["pdf"],
    accept_multiple_files=False,
    help="Upload a PDF file containing quantum physics material."
)

# Upload Image
uploaded_image = st.file_uploader(
    "Upload an image (optional):",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help="Upload an image with quantum content (e.g., textbook scan, notes)."
)

# Process PDF
pdf_context = None
if uploaded_file is not None:
    try:
        pdf_context = extract_text_from_pdf(uploaded_file)
        if not pdf_context:
            st.warning("Uploaded PDF seems empty or unreadable.")
        else:
            st.info("PDF summarized and context is ready!")
    except Exception as e:
        st.error(f"Error processing PDF: {e}")

# Process Image
image_context = None
if uploaded_image is not None:
    image_context = extract_text_from_image(uploaded_image)
    if not image_context:
        st.warning("Uploaded image seems to contain no readable text.")
    else:
        st.info("Image processed and context is ready!")

# Groq Query Function
def ask_groq(prompt, api_key, context_text=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    full_prompt = f"Context:\n{context_text}\n\nQuestion:\n{prompt}" if context_text else prompt
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": 
             "You are a helpful quantum physics assistant. Always explain concepts clearly and deeply. "
             "When writing math, wrap entire equations using a single block math `$$ ... $$`. "
             "Do not split matrix multiplications or subtractions into multiple `$$` blocks — always put the whole equation inside one `$$ ... $$` block."
            },
            {"role": "user", "content": full_prompt}
        ]
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

# Button logic
if st.button("Ask"):
    if not api_key:
        st.error("Please enter your Groq API Key.")
    elif not user_question:
        st.warning("Please enter a question.")
    else:
        combined_context = ""
        if pdf_context:
            combined_context += f"[PDF Context]\n{pdf_context}\n\n"
        if image_context:
            combined_context += f"[Image Context]\n{image_context}\n"

        with st.spinner("Thinking..."):
            answer = ask_groq(user_question, api_key, combined_context if combined_context else None)
            clean_and_display_grok_reply(answer)
