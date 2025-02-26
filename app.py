import streamlit as st
import PyPDF2
from textblob import TextBlob
from gramformer import Gramformer
import torch
import re
import pandas as pd
import time
import tempfile
import os 
os.system("pip uninstall -y pydantic")
os.system("pip install pydantic==1.10.12 --quiet")
os.system("python -m spacy download en_core_web_sm")
# Initialize Gramformer model (Grammar correction)
gf = Gramformer(models=1, use_gpu=torch.cuda.is_available())

# Utility to fix contractions
def fix_contractions(text):
    contractions = {"dont": "don't", "its": "it's", "im": "I'm", "doesnt": "doesn't"}
    pattern = re.compile(r'\b(' + '|'.join(contractions.keys()) + r')\b')
    return pattern.sub(lambda x: contractions[x.group()], text)

# Correct grammar and spelling
def correct_text(text):
    # Grammar correction using Gramformer
    corrected_sentences = []
    original_sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in original_sentences:
        corrected = gf.correct(sentence)
        corrected_sentences.append(list(corrected)[0] if corrected else sentence)
    
    # Spelling correction using TextBlob
    spelling_corrected = str(TextBlob(' '.join(corrected_sentences)).correct())
    return spelling_corrected, ' '.join(corrected_sentences)

# Highlight corrections
def highlight_changes(original, corrected):
    original_words = original.split()
    corrected_words = corrected.split()
    highlighted = []
    for o, c in zip(original_words, corrected_words):
        if o != c:
            highlighted.append(f"<span style='color: red'><b>{c}</b></span>")
        else:
            highlighted.append(o)
    return ' '.join(highlighted)

# Extract word-level changes
def extract_changes(original, corrected):
    original_words = original.split()
    corrected_words = corrected.split()
    changes = []

    for o, c in zip(original_words, corrected_words):
        if o != c:
            changes.append({"Original Word": o, "Corrected Word": c})

    return changes

# Analyze corrections
def analyze_corrections(original, corrected):
    original_words = original.split()
    corrected_words = corrected.split()
    spelling_changes = 0
    grammar_changes = 0

    for o, c in zip(original_words, corrected_words):
        if o != c:
            if TextBlob(o).correct() == c:
                spelling_changes += 1
            else:
                grammar_changes += 1

    return spelling_changes, grammar_changes

# Streamlit App UI
st.title("📝 Advanced Grammar and Spelling Correction App with Word Changes")
st.write("Upload a PDF or input text to correct grammar, spelling, and view analytics with detailed word changes.")

# Input Section
uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])
input_text = st.text_area("Or Paste Your Text Here", "")

if st.button("Correct Text"):
    text = ""
    with st.spinner("Processing with AI... Please wait!"):
        time.sleep(1)

        # Extract text from PDF or input
        if uploaded_pdf:
            try:
                reader = PyPDF2.PdfReader(uploaded_pdf)
                text = ' '.join(page.extract_text() for page in reader.pages if page.extract_text())
                st.info("✅ PDF text extracted successfully!")
            except Exception as e:
                st.error(f"❌ Error extracting text from PDF: {e}")
                st.stop()
        elif input_text.strip():
            text = input_text
        else:
            st.warning("⚠️ Please upload a PDF or input text to proceed.")
            st.stop()

        # Fix contractions
        original_text = fix_contractions(text)

        # Correct Text
        corrected_text, grammar_corrected_text = correct_text(original_text)

        # Highlight changes
        highlighted_text = highlight_changes(original_text, corrected_text)

        # Extract word-level changes
        word_changes = extract_changes(original_text, corrected_text)

        # Analyze corrections
        spelling_changes, grammar_changes = analyze_corrections(original_text, corrected_text)

        # Total changes
        total_changes = spelling_changes + grammar_changes

        # Display results
        st.subheader("📄 Original Text")
        st.write(original_text)

        st.subheader("✏️ Corrected Text (Changes Highlighted in Red)")
        st.markdown(highlighted_text, unsafe_allow_html=True)

        # Display Word Change List
        if word_changes:
            st.subheader("📝 List of Changed Words")
            changes_df = pd.DataFrame(word_changes)
            st.table(changes_df)
        else:
            st.info("✅ No word-level changes detected.")

        # Display Analytics with Streamlit
        st.subheader("📊 Correction Analytics")
        corrections_df = pd.DataFrame({
            "Correction Type": ["Spelling", "Grammar"],
            "Count": [spelling_changes, grammar_changes]
        })
        st.bar_chart(corrections_df.set_index("Correction Type"))

        st.write(f"**Total Corrections:** {total_changes}")

        # Save report to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt") as tmp_file:
            tmp_file.write("Corrected Text:\n")
            tmp_file.write("====================\n")
            tmp_file.write(corrected_text)
            tmp_file_path = tmp_file.name

        st.success("📥 Correction report generated successfully!")
        with open(tmp_file_path, "rb") as file:
            st.download_button("Download Report", data=file, file_name="correction_report.txt")