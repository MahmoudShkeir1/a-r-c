import streamlit as st
import pdfplumber
import docx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# App title
st.title("📄 AI Resume Checker")

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# Paste job description or keyword list
st.markdown("### 💼 Enter Job Description or Keywords")
job_description = st.text_area("Paste the job description here, or list keywords separated by commas")

# Helper: Read PDF
def read_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text.lower()

# Helper: Read DOCX
def read_docx(file):
    doc = docx.Document(file)
    full_text = "\n".join([para.text for para in doc.paragraphs])
    return full_text.lower()

# Improved keyword extractor
def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    sentences = sent_tokenize(text.lower())
    keywords = set()

    for sent in sentences:
        words = word_tokenize(sent)
        words = [word for word in words if word.isalpha() and word not in stop_words]

        for i in range(len(words)):
            # single word
            keywords.add(words[i])
            # two-word phrase
            if i + 1 < len(words):
                keywords.add(f"{words[i]} {words[i+1]}")
            # three-word phrase
            if i + 2 < len(words):
                keywords.add(f"{words[i]} {words[i+1]} {words[i+2]}")

    clean_keywords = [kw.strip() for kw in keywords if 1 <= len(kw.split()) <= 3 and len(kw) < 40]
    return sorted(set(clean_keywords))

# Main logic
if uploaded_file and job_description:
    # Extract resume text
    file_type = uploaded_file.name.split(".")[-1]
    if file_type == "pdf":
        resume_text = read_pdf(uploaded_file)
    elif file_type == "docx":
        resume_text = read_docx(uploaded_file)
    else:
        st.error("Unsupported file type.")
        resume_text = ""

    # Extract keywords from job description or keyword list
    if "," in job_description:
        target_keywords = [kw.strip().lower() for kw in job_description.split(",") if kw.strip()]
    else:
        target_keywords = extract_keywords(job_description)

    st.subheader("🔍 Extracted Target Keywords")
    st.write(", ".join(target_keywords))

    if resume_text:
        st.subheader("📝 Extracted Resume Text")
        st.text_area("Resume Content", resume_text, height=300)

        # Keyword match analysis
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
                st.markdown(f"- Consider including or elaborating on: **'{tip}'** if it's relevant.")

        # Downloadable report
        report = f"Resume Keyword Match Report\n"
        report += f"{'-'*30}\n"
        report += f"Matched Keywords ({len(matched_keywords)}/{len(target_keywords)}):\n"
        report += ", ".join(matched_keywords) + "\n\n"
        report += f"Score: {match_score}%\n\n"

        if match_score < 100:
            report += "Suggestions to Improve:\n"
            for tip in missing:
                report += f"- Add or expand on: {tip}\n"
        else:
            report += "Great job! All key terms matched.\n"

        st.download_button(
            label="📥 Download Match Report",
            data=report,
            file_name="resume_score_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not extract text from the resume.")
