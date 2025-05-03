import streamlit as st
import os
import requests
import PyPDF2
import re

# Streamlit App Title
st.title("QuantumQuery (Powered by Groq)")
st.write("Ask me anything about Quantum Physics! Optionally, upload a PDF for extra context.")

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
    # Split sentences using regex
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

# Upload PDF
uploaded_file = st.file_uploader(
    "Or upload a PDF for me to read:",
    type=["pdf"],
    accept_multiple_files=False,
    help="Upload a PDF file containing quantum physics material."
)

# Display summarized PDF text
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
            {"role": "system", "content": "You are a helpful quantum physics assistant. Explain concepts clearly and deeply. If answering anything that requires math use latex unless otherwise instructed."},
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
        with st.spinner("Thinking..."):
            answer = ask_groq(user_question, api_key, pdf_context)
            st.success(answer)
