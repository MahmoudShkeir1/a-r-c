import streamlit as st
import pdfplumber
import docx
import nltk
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import torch
from transformers import BertTokenizer, BertModel
import matplotlib.pyplot as plt
from fpdf import FPDF

# Download required NLTK resources (run once per environment)
nltk.download('punkt')
nltk.download('stopwords')

# Load SpaCy model (pre-installed via requirements.txt)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model 'en_core_web_sm' is not installed. Please check your requirements.txt.")
    st.stop()

# Load BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# App title
st.title("📄 AI Resume Checker")

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# Paste job description or keyword list
st.markdown("### 💼 Enter Job Description or Keywords")
job_description = st.text_area("Paste the job description here, or list keywords separated by commas")

# Helper: Read PDF
def read_pdf(file):
    try:
        with pdfplumber.open(file) as pdf:
            return " ".join([page.extract_text() or "" for page in pdf.pages]).lower()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Helper: Read DOCX
def read_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs]).lower()
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

# Extract Named Entities (for better keyword matching)
def extract_named_entities(text):
    doc = nlp(text)
    return set([ent.text.lower() for ent in doc.ents])

# Improved keyword extractor
def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    sentences = sent_tokenize(text.lower())
    keywords = set()

    for sent in sentences:
        words = [word for word in word_tokenize(sent) if word.isalpha() and word not in stop_words]
        for i in range(len(words)):
            keywords.add(words[i])
            if i + 1 < len(words):
                keywords.add(f"{words[i]} {words[i+1]}")
            if i + 2 < len(words):
                keywords.add(f"{words[i]} {words[i+1]} {words[i+2]}")

    return sorted([kw for kw in keywords if 1 <= len(kw.split()) <= 3 and len(kw) < 40])

# Function to calculate similarity using BERT
def get_similarity(text1, text2):
    inputs1 = tokenizer(text1, return_tensors='pt')
    inputs2 = tokenizer(text2, return_tensors='pt')
    with torch.no_grad():
        outputs1 = model(**inputs1)
        outputs2 = model(**inputs2)
    similarity = torch.cosine_similarity(outputs1[0][0], outputs2[0][0], dim=0)
    return similarity.item()

# Plot Match Score
def plot_match_score(match_score, total_keywords):
    fig, ax = plt.subplots()
    ax.barh(["Match Score"], [match_score])
    ax.set_xlim(0, total_keywords)
    ax.set_title("Keyword Match Score")
    st.pyplot(fig)

# Main logic
if uploaded_file and job_description:
    file_type = uploaded_file.name.split(".")[-1]
    resume_text = read_pdf(uploaded_file) if file_type == "pdf" else read_docx(uploaded_file)

    target_keywords = (
        [kw.strip().lower() for kw in job_description.split(",") if kw.strip()]
        if "," in job_description
        else extract_keywords(job_description)
    )

    st.subheader("🔍 Extracted Target Keywords")
    st.write(", ".join(target_keywords))

    if resume_text:
        st.subheader("📝 Extracted Resume Text")
        st.text_area("Resume Content", resume_text, height=300)

        matched_keywords = [kw for kw in target_keywords if kw in resume_text]
        match_score = int(len(matched_keywords) / len(target_keywords) * 100) if target_keywords else 0

        st.subheader("📌 Keyword Match Analysis")
        st.write(f"✅ **Matched Keywords ({len(matched_keywords)}/{len(target_keywords)}):**")
        st.write(", ".join(matched_keywords))
        st.progress(match_score / 100)
        st.success(f"Your resume matches **{match_score}%** of the job-specific keywords.")

        if match_score < 100:
            missing = [kw for kw in target_keywords if kw not in matched_keywords]
            st.subheader("💡 Suggestions for Improvement:")
            for tip in missing:
                st.markdown(f"- Consider including or elaborating on: **'{tip}'**")

            plot_match_score(match_score, len(target_keywords))

        # Create and download report
        report = f"Resume Keyword Match Report\n{'-'*30}\n"
        report += f"Matched Keywords ({len(matched_keywords)}/{len(target_keywords)}):\n"
        report += ", ".join(matched_keywords) + "\n\n"
        report += f"Score: {match_score}%\n\n"
        report += "Suggestions to Improve:\n" if match_score < 100 else "Great job! All key terms matched.\n"
        for tip in missing:
            report += f"- Add or expand on: {tip}\n"

        st.download_button(
            label="📥 Download Match Report",
            data=report,
            file_name="resume_score_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not extract text from the resume.")
