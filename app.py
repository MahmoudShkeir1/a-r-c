import streamlit as st
import pdfplumber
import docx
import nltk
import spacy
from spacy.cli import download
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Load or download SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

st.title("📄 Simplified AI Resume Checker")

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# Input job description
job_description = st.text_area("💼 Paste Job Description or Keywords (comma-separated)", height=200)

def read_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages]).lower()

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs]).lower()

def extract_keywords(text):
    stop_words = set(stopwords.words("english"))
    tokens = word_tokenize(text.lower())
    return sorted(set([word for word in tokens if word.isalpha() and word not in stop_words]))

def plot_score(score, total):
    fig, ax = plt.subplots()
    ax.barh(["Match Score"], [score])
    ax.set_xlim(0, total)
    ax.set_title("Keyword Match")
    st.pyplot(fig)

if uploaded_file and job_description:
    ext = uploaded_file.name.split(".")[-1]
    resume_text = read_pdf(uploaded_file) if ext == "pdf" else read_docx(uploaded_file)

    target_keywords = (
        [kw.strip().lower() for kw in job_description.split(",")]
        if "," in job_description else extract_keywords(job_description)
    )

    matched = [kw for kw in target_keywords if kw in resume_text]
    score = int(len(matched) / len(target_keywords) * 100) if target_keywords else 0

    st.subheader("✅ Matched Keywords")
    st.write(", ".join(matched))
    st.success(f"Match Score: {score}%")

    if score < 100:
        missing = [kw for kw in target_keywords if kw not in matched]
        st.subheader("🛠 Suggestions:")
        for m in missing:
            st.write(f"- Consider including: **{m}**")

    plot_score(len(matched), len(target_keywords))
