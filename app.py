import streamlit as st
import pdfplumber
import docx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import streamlit_authenticator as stauth

# Set up user credentials (this is a simple example, you could also store this info securely)
usernames = ['user1', 'user2']
passwords = ['password1', 'password2']

# Encrypt passwords for security
hashed_passwords = stauth.Hasher(passwords).generate()

# Authentication instance
authenticator = stauth.Authenticate(
    usernames, 
    hashed_passwords, 
    'your_cookie_name', 
    'your_signature_key', 
    cookie_expiry_days=30
)

# Authentication
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Your original app code goes here if user is authenticated
    st.title("📄 AI Resume Checker")

    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

    st.markdown("### 💼 Enter Job Description or Keywords")
    job_description = st.text_area("Paste the job description here, or list keywords separated by commas")

    def read_pdf(file):
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text.lower()

    def read_docx(file):
        doc = docx.Document(file)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        return full_text.lower()

    def extract_keywords(text):
        stop_words = set(stopwords.words('english'))
        sentences = sent_tokenize(text.lower())
        keywords = set()

        for sent in sentences:
            words = word_tokenize(sent)
            words = [word for word in words if word.isalpha() and word not in stop_words]

            for i in range(len(words)):
                keywords.add(words[i])
                if i + 1 < len(words):
                    keywords.add(f"{words[i]} {words[i+1]}")
                if i + 2 < len(words):
                    keywords.add(f"{words[i]} {words[i+1]} {words[i+2]}")

        clean_keywords = [kw.strip() for kw in keywords if 1 <= len(kw.split()) <= 3 and len(kw) < 40]
        return sorted(set(clean_keywords))

    if uploaded_file and job_description:
        file_type = uploaded_file.name.split(".")[-1]
        if file_type == "pdf":
            resume_text = read_pdf(uploaded_file)
        elif file_type == "docx":
            resume_text = read_docx(uploaded_file)
        else:
            st.error("Unsupported file type.")
            resume_text = ""

        if "," in job_description:
            target_keywords = [kw.strip().lower() for kw in job_description.split(",") if kw.strip()]
        else:
            target_keywords = extract_keywords(job_description)

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
                    st.markdown(f"- Consider including or elaborating on: **'{tip}'** if it's relevant.")

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
else:
    if authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')
