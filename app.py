import streamlit as st
import os
import requests
import PyPDF2
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

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

# Summarization Function
def summarize_text(text, num_sentences=5):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

# PDF Extractor + Summarizer
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    pdf_text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            pdf_text += page_text
    if pdf_text:
        return summarize_text(pdf_text, num_sentences=5)
    else:
        return ""

# Upload PDF
uploaded_file = st.file_uploader(
    "Or upload a PDF for me to read:",
    type="pdf",
    accept_multiple_files=False,
    help="Upload a PDF file containing quantum physics material."
)

# Display summarized PDF text
pdf_context = None
if uploaded_file is not None:
    uploaded_file.seek(0)  # Reset pointer
    pdf_context = extract_text_from_pdf(uploaded_file)
    st.text_area("Summarized PDF Context:", pdf_context, height=200)

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
            {"role": "system", "content": "You are a helpful quantum physics assistant. Explain concepts clearly and deeply."},
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
